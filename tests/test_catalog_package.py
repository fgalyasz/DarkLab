import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.catalog.catalog_settings import read_catalog_setting, write_catalog_setting
from src.catalog.database import create_catalog, open_catalog
from src.catalog.folders import add_imported_folder, imported_folders
from src.catalog.index_images import list_index_images, read_index_image, write_index_image
from src.catalog.locations import PREVIEWS_NAME, SETTINGS_NAME, database_file
from src.catalog.session import catalog_to_reopen, remember_catalog


def legacy_catalog(folder: Path) -> Path:
    path = folder / "old.darklab"
    connection = sqlite3.connect(path)
    try:
        _write_legacy_schema(connection)
    finally:
        connection.close()
    return path


def _write_legacy_schema(connection: sqlite3.Connection) -> None:
    connection.execute("CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT)")
    connection.execute("INSERT INTO catalog_meta (key, value) VALUES ('schema', '1')")
    connection.commit()


class CatalogPackageTests(unittest.TestCase):
    def test_package_holds_folder_index_and_setting(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        other = create_catalog(Path(tempfile.mkdtemp()) / "personal")
        add_imported_folder(catalog, Path("/shoots/wedding"))
        add_imported_folder(catalog, Path("/shoots/wedding"))
        write_index_image(catalog, 4, b"jpeg")
        write_catalog_setting(catalog, "preview_size", "standard")
        self.assertEqual(imported_folders(catalog), ["/shoots/wedding"])
        self.assertEqual(read_index_image(catalog, 4), b"jpeg")
        self.assertEqual(read_catalog_setting(catalog, "preview_size"), "standard")
        self.assertEqual(read_catalog_setting(database_file(catalog), "preview_size"), "standard")
        self.assertEqual(read_index_image(database_file(catalog), 4), b"jpeg")
        self.assertEqual(imported_folders(other), [])
        self.assertIsNone(read_catalog_setting(other, "preview_size"))

    def test_create_again_keeps_the_package(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        write_catalog_setting(catalog, "preview_size", "standard")
        write_index_image(catalog, 1, b"jpeg")
        self.assertEqual(create_catalog(catalog), catalog)
        self.assertEqual(read_catalog_setting(catalog, "preview_size"), "standard")
        self.assertEqual(read_index_image(catalog, 1), b"jpeg")

    def test_index_list_is_empty_until_images_exist(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        self.assertEqual(list_index_images(catalog), [])
        second = write_index_image(catalog, 2, b"b")
        first = write_index_image(catalog, 1, b"a")
        (catalog / "previews" / "note.txt").write_text("x", encoding="utf-8")
        self.assertEqual(list_index_images(catalog), [first, second])
        legacy = legacy_catalog(Path(tempfile.mkdtemp()))
        self.assertEqual(list_index_images(legacy), [])

    def test_missing_index_and_unknown_setting(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        self.assertIsNone(read_index_image(catalog, 9))
        self.assertIsNone(read_catalog_setting(catalog, "missing"))

    def test_empty_folder_and_bad_photo_id_are_refused(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        with self.assertRaises(ValueError):
            add_imported_folder(catalog, Path(" "))
        with self.assertRaises(ValueError):
            write_index_image(catalog, 0, b"jpeg")

    def test_empty_setting_name_is_refused(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        with self.assertRaises(ValueError):
            write_catalog_setting(catalog, " ", "standard")

    def test_invalid_settings_are_refused(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        (catalog / SETTINGS_NAME).write_text("[1]\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_catalog_setting(catalog, "preview_size")
        (catalog / SETTINGS_NAME).write_text("{", encoding="utf-8")
        with self.assertRaises(ValueError):
            read_catalog_setting(catalog, "preview_size")

    def test_deleted_previews_leave_the_catalog(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        add_imported_folder(catalog, Path("/shoots/wedding"))
        write_catalog_setting(catalog, "preview_size", "standard")
        write_index_image(catalog, 1, b"jpeg")
        shutil.rmtree(catalog / PREVIEWS_NAME)
        self.assertEqual(open_catalog(catalog), catalog)
        self.assertEqual(imported_folders(catalog), ["/shoots/wedding"])
        self.assertEqual(read_catalog_setting(catalog, "preview_size"), "standard")
        self.assertIsNone(read_index_image(catalog, 1))

    def test_missing_settings_file_reads_empty(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        (catalog / SETTINGS_NAME).unlink()
        self.assertIsNone(read_catalog_setting(catalog, "preview_size"))

    def test_create_on_a_legacy_file_keeps_the_file(self) -> None:
        path = legacy_catalog(Path(tempfile.mkdtemp()))
        self.assertEqual(create_catalog(path), path)
        self.assertTrue(path.is_file())

    def test_legacy_file_still_opens(self) -> None:
        path = legacy_catalog(Path(tempfile.mkdtemp()))
        self.assertEqual(open_catalog(path), path)
        self.assertEqual(catalog_to_reopen(remember_catalog({}, path)), path)
        self.assertTrue(database_file(path).is_file())

    def test_directory_without_a_database_is_not_reopened(self) -> None:
        folder = Path(tempfile.mkdtemp()) / "empty.darklab"
        folder.mkdir()
        self.assertIsNone(catalog_to_reopen({"catalog_path": str(folder)}))
