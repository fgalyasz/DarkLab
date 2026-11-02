import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.catalog.backup import BackupError, backup_catalog, list_backups
from src.catalog.database import create_catalog, open_catalog
from src.catalog.integrity import CatalogIntegrityError, check_integrity, require_healthy
from src.catalog.locations import database_file

TORN_BYTES = b"SQLite format 3\x00" + b"\xff" * 4096
GARBAGE_BYTES = b"this is not a database at all" * 200


def _tear(catalog: Path, content: bytes = GARBAGE_BYTES) -> None:
    database_file(catalog).write_bytes(content)


def _corrupt_pages(catalog: Path) -> None:
    database = database_file(catalog)
    data = bytearray(database.read_bytes())
    data[len(data) // 2:] = b"\xff" * (len(data) - len(data) // 2)
    database.write_bytes(bytes(data))


def _fill_photos(catalog: Path, count: int) -> None:
    connection = sqlite3.connect(database_file(catalog))
    connection.executemany(
        "INSERT INTO photos (original_path, content_hash) VALUES (?, ?)",
        [(f"/shoot/{index}.jpg", f"hash-{index}" * 20) for index in range(count)],
    )
    connection.commit()
    connection.close()


class IntegrityCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.catalog = create_catalog(self.folder / "shoot")

    def test_healthy_catalog_passes_quick_and_full(self) -> None:
        for full in (False, True):
            report = check_integrity(self.catalog, full)
            self.assertTrue(report.healthy)
            self.assertEqual(report.full, full)
            self.assertIn("passed", report.describe())

    def test_report_names_the_kind_of_check(self) -> None:
        self.assertIn("quick", check_integrity(self.catalog).describe())
        self.assertIn("full", check_integrity(self.catalog, True).describe())

    def test_torn_file_is_reported_with_a_reason(self) -> None:
        _tear(self.catalog)
        report = check_integrity(self.catalog)
        self.assertFalse(report.healthy)
        self.assertIn("failed", report.describe())
        self.assertIn(str(self.catalog), report.describe())

    def test_damaged_pages_fail_the_full_check(self) -> None:
        _fill_photos(self.catalog, 400)
        _corrupt_pages(self.catalog)
        self.assertFalse(check_integrity(self.catalog, True).healthy)

    def test_missing_database_is_unhealthy_and_not_created(self) -> None:
        database_file(self.catalog).unlink()
        self.assertFalse(check_integrity(self.catalog).healthy)
        self.assertFalse(database_file(self.catalog).exists())

    def test_report_lists_only_the_first_problems(self) -> None:
        problems = tuple(f"problem {index}" for index in range(9))
        with patch("src.catalog.integrity._run_pragma", return_value=list(problems)):
            text = check_integrity(self.catalog).describe()
        self.assertIn("problem 4", text)
        self.assertNotIn("problem 5", text)

    def test_require_healthy_returns_the_report(self) -> None:
        self.assertTrue(require_healthy(self.catalog).healthy)

    def test_require_healthy_raises_a_value_error_for_a_torn_file(self) -> None:
        _tear(self.catalog, TORN_BYTES)
        with self.assertRaises(CatalogIntegrityError) as context:
            require_healthy(self.catalog)
        self.assertIsInstance(context.exception, ValueError)


class OpenAndBackupIntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.catalog = create_catalog(self.folder / "shoot")

    def test_open_accepts_a_healthy_catalog(self) -> None:
        self.assertEqual(open_catalog(self.catalog), self.catalog)

    def test_open_refuses_a_torn_catalog(self) -> None:
        _tear(self.catalog)
        with self.assertRaises(CatalogIntegrityError):
            open_catalog(self.catalog)

    def test_open_still_reports_a_missing_catalog(self) -> None:
        with self.assertRaises(FileNotFoundError):
            open_catalog(self.folder / "absent.darklab")

    def test_open_still_rejects_a_foreign_database(self) -> None:
        foreign = self.folder / "foreign.darklab"
        foreign.mkdir()
        sqlite3.connect(foreign / "catalog.sqlite").close()
        with self.assertRaises(ValueError):
            open_catalog(foreign)

    def test_backup_of_a_healthy_catalog_succeeds_with_full_check(self) -> None:
        backup = backup_catalog(self.catalog, self.folder / "backups", full_check=True)
        self.assertEqual(list_backups(self.folder / "backups"), [backup])

    def test_backup_refuses_a_torn_catalog_and_writes_nothing(self) -> None:
        _tear(self.catalog)
        with self.assertRaises(BackupError) as context:
            backup_catalog(self.catalog, self.folder / "backups")
        self.assertIn("Backup refused", str(context.exception))
        self.assertEqual(list_backups(self.folder / "backups"), [])
        self.assertFalse((self.folder / "backups").exists())

    def test_full_backup_check_refuses_damaged_pages(self) -> None:
        _fill_photos(self.catalog, 400)
        _corrupt_pages(self.catalog)
        with self.assertRaises(BackupError):
            backup_catalog(self.catalog, self.folder / "backups", full_check=True)
        self.assertEqual(list_backups(self.folder / "backups"), [])


if __name__ == "__main__":
    unittest.main()
