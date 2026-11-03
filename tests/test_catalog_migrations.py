import os
import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.catalog.backup import BackupError, default_backup_root, list_backups
from src.catalog.database import create_catalog, open_catalog, read_schema
from src.catalog.locations import database_file
from src.catalog.migrations import CatalogMigrationError, migrate_catalog
from src.catalog.schema_sql import CURRENT_SCHEMA

MOMENT = datetime(2026, 11, 3, 20, 15, 0)
MIGRATIONS_TARGET = "src.catalog.migrations.MIGRATIONS"
CURRENT_TARGET = "src.catalog.migrations.CURRENT_SCHEMA"
BACKUP_TARGET = "src.catalog.migrations.backup_catalog"
VERSION_ONE_PHOTOS = "CREATE TABLE photos (id INTEGER PRIMARY KEY, original_path TEXT)"


def _version_one_catalog(folder: Path, with_photos: bool = True) -> Path:
    path = folder / "old.darklab"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT)")
    connection.execute("INSERT INTO catalog_meta (key, value) VALUES ('schema', '1')")
    if with_photos:
        connection.execute(VERSION_ONE_PHOTOS)
        connection.execute("INSERT INTO photos (original_path) VALUES ('/shoot/a.jpg')")
    connection.commit()
    connection.close()
    return path


def _columns(catalog: Path, table: str) -> set[str]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        return {str(row[1]) for row in connection.execute(f"PRAGMA table_info({table})")}
    finally:
        connection.close()


def _fresh_catalog(folder: Path) -> Path:
    return create_catalog(folder / "fresh")


class UpMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())

    def test_open_upgrades_a_version_one_catalog_to_the_current_schema(self) -> None:
        catalog = _version_one_catalog(self.folder)
        self.assertEqual(open_catalog(catalog), catalog)
        self.assertEqual(read_schema(catalog), str(CURRENT_SCHEMA))
        self.assertIn("develop_settings", _columns(catalog, "photos"))
        self.assertIn("folders", _tables(catalog))

    def test_upgrade_keeps_existing_photos(self) -> None:
        catalog = _version_one_catalog(self.folder)
        open_catalog(catalog)
        connection = sqlite3.connect(catalog)
        rows = connection.execute("SELECT original_path FROM photos").fetchall()
        connection.close()
        self.assertEqual(rows, [("/shoot/a.jpg",)])

    def test_upgrade_creates_a_missing_photo_table(self) -> None:
        catalog = _version_one_catalog(self.folder, with_photos=False)
        open_catalog(catalog)
        self.assertIn("content_hash", _columns(catalog, "photos"))

    def test_upgrade_backs_up_before_changing_anything(self) -> None:
        catalog = _version_one_catalog(self.folder)
        migrate_catalog(catalog, "1", MOMENT)
        backups = list_backups(default_backup_root(catalog))
        self.assertEqual([path.name for path in backups], ["old-20261103-201500.darklab"])
        self.assertNotIn("develop_settings", _columns(backups[0], "photos"))
        self.assertEqual(read_schema(backups[0]), "1")

    def test_current_schema_needs_no_migration_and_no_backup(self) -> None:
        catalog = _fresh_catalog(self.folder)
        self.assertFalse(migrate_catalog(catalog, str(CURRENT_SCHEMA)))
        self.assertEqual(list_backups(default_backup_root(catalog)), [])

    def test_migrating_reports_that_work_was_done(self) -> None:
        catalog = _version_one_catalog(self.folder)
        self.assertTrue(migrate_catalog(catalog, "1", MOMENT))

    def test_second_open_does_not_back_up_again(self) -> None:
        catalog = _version_one_catalog(self.folder)
        open_catalog(catalog)
        open_catalog(catalog)
        self.assertEqual(len(list_backups(default_backup_root(catalog))), 1)

    def test_several_steps_run_in_order_and_store_each_version(self) -> None:
        catalog = _version_one_catalog(self.folder)
        order: list[int] = []
        steps = {1: lambda connection: order.append(1), 2: lambda connection: order.append(2)}
        with patch(MIGRATIONS_TARGET, steps), patch(CURRENT_TARGET, 3):
            migrate_catalog(catalog, "1", MOMENT)
        self.assertEqual(order, [1, 2])
        self.assertEqual(read_schema(catalog), "3")


class RefusedMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())

    def test_newer_catalog_is_refused_and_left_alone(self) -> None:
        catalog = _fresh_catalog(self.folder)
        with self.assertRaises(CatalogMigrationError) as context:
            migrate_catalog(catalog, str(CURRENT_SCHEMA + 1))
        self.assertIn("Update DarkLab", str(context.exception))
        self.assertEqual(list_backups(default_backup_root(catalog)), [])

    def test_open_refuses_a_catalog_from_a_newer_app(self) -> None:
        catalog = _fresh_catalog(self.folder)
        _store_schema(catalog, str(CURRENT_SCHEMA + 1))
        with self.assertRaises(ValueError):
            open_catalog(catalog)
        self.assertEqual(read_schema(catalog), str(CURRENT_SCHEMA + 1))

    def test_unreadable_schema_value_is_refused(self) -> None:
        catalog = _fresh_catalog(self.folder)
        with self.assertRaises(CatalogMigrationError) as context:
            migrate_catalog(catalog, "two")
        self.assertIn("unreadable schema", str(context.exception))

    def test_schema_with_no_upgrade_path_is_refused(self) -> None:
        catalog = _version_one_catalog(self.folder)
        with self.assertRaises(CatalogMigrationError) as context:
            migrate_catalog(catalog, "0")
        self.assertIn("no upgrade path", str(context.exception))
        self.assertEqual(read_schema(catalog), "1")

    def test_failed_backup_stops_the_upgrade(self) -> None:
        catalog = _version_one_catalog(self.folder)
        with patch(BACKUP_TARGET, side_effect=BackupError("disk full")):
            with self.assertRaises(CatalogMigrationError) as context:
                migrate_catalog(catalog, "1", MOMENT)
        self.assertIn("no backup was made", str(context.exception))
        self.assertEqual(read_schema(catalog), "1")
        self.assertNotIn("develop_settings", _columns(catalog, "photos"))


class FailedMigrationTests(unittest.TestCase):
    def test_failing_step_rolls_back_every_change_and_keeps_the_backup(self) -> None:
        catalog = _version_one_catalog(Path(tempfile.mkdtemp()))
        steps = {1: _add_column_then_fail}
        with patch(MIGRATIONS_TARGET, steps):
            with self.assertRaises(CatalogMigrationError) as context:
                migrate_catalog(catalog, "1", MOMENT)
        self.assertIn("failed", str(context.exception))
        self.assertEqual(read_schema(catalog), "1")
        self.assertNotIn("develop_settings", _columns(catalog, "photos"))
        self.assertEqual(len(list_backups(default_backup_root(catalog))), 1)


def _add_column_then_fail(connection: sqlite3.Connection) -> None:
    connection.execute("ALTER TABLE photos ADD COLUMN develop_settings TEXT")
    connection.execute("SELECT * FROM table_that_does_not_exist")


def _tables(catalog: Path) -> set[str]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    finally:
        connection.close()
    return {str(row[0]) for row in rows}


def _store_schema(catalog: Path, value: str) -> None:
    connection = sqlite3.connect(database_file(catalog))
    connection.execute("UPDATE catalog_meta SET value = ? WHERE key = 'schema'", (value,))
    connection.commit()
    connection.close()


if __name__ == "__main__":
    unittest.main()
