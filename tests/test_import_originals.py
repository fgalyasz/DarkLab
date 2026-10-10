import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import rawpy
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.catalog.database import apply_schema, create_catalog, original_paths
from src.catalog.locations import database_file
from src.catalog.photos import stored_hash
from src.catalog.folders import imported_folders
from src.catalog.index_images import list_index_images, read_index_image
from src.importing.originals import _raw_thumb_bytes, import_originals, is_duplicate


def _thumb(fmt: rawpy.ThumbFormat, data: object) -> MagicMock:
    thumb = MagicMock()
    thumb.format = fmt
    thumb.data = data
    return thumb


def _thumb_bytes(thumb: MagicMock) -> bytes:
    raw = MagicMock()
    raw.extract_thumb.return_value = thumb
    raw.__enter__.return_value = raw
    with patch("src.importing.originals.rawpy.imread", return_value=raw):
        return _raw_thumb_bytes(Path("frame.arw"))


def _legacy_photos(database: Path) -> None:
    connection = sqlite3.connect(database)
    try:
        connection.execute("CREATE TABLE photos (id INTEGER PRIMARY KEY, original_path TEXT)")
        connection.execute("INSERT INTO photos (original_path) VALUES (?)", ("/shoots/a.jpg",))
        connection.commit()
    finally:
        connection.close()


def _insert_without_hash(catalog: Path, original: Path) -> None:
    connection = sqlite3.connect(database_file(catalog))
    try:
        connection.execute("INSERT INTO photos (original_path) VALUES (?)", (str(original),))
        connection.commit()
    finally:
        connection.close()


def tiny_jpeg(folder: Path, name: str, color: tuple[int, int, int] = (20, 40, 60)) -> Path:
    path = folder / name
    Image.new("RGB", (8, 6), color).save(path, format="JPEG")
    return path


class ImportOriginalTests(unittest.TestCase):
    def test_import_writes_an_index_image(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        first = tiny_jpeg(root, "a.jpg")
        second = tiny_jpeg(root, "b.jpg", (90, 10, 10))
        self.assertEqual(import_originals(catalog, [first, second, first]), 2)
        self.assertEqual(original_paths(catalog), [str(first), str(second)])
        self.assertEqual(imported_folders(catalog), [str(root)])
        indexes = list_index_images(catalog)
        self.assertEqual(len(indexes), 2)
        self.assertTrue(read_index_image(catalog, 1).startswith(b"\xff\xd8"))

    def test_same_bytes_are_skipped_unless_requested(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        first = tiny_jpeg(root, "a.jpg")
        second = root / "b.jpg"
        second.write_bytes(first.read_bytes())
        self.assertEqual(import_originals(catalog, [first]), 1)
        digest = stored_hash(catalog, first)
        self.assertEqual(import_originals(catalog, [first], allow_duplicate=True), 0)
        self.assertEqual(stored_hash(catalog, first), digest)
        self.assertEqual(import_originals(catalog, [second]), 0)
        self.assertEqual(original_paths(catalog), [str(first)])
        self.assertEqual(stored_hash(catalog, first), digest)
        self.assertEqual(len(list_index_images(catalog)), 1)
        self.assertEqual(import_originals(catalog, [second], allow_duplicate=True), 1)
        self.assertEqual(original_paths(catalog), [str(first), str(second)])
        self.assertEqual(len(list_index_images(catalog)), 2)

    def test_missing_hash_is_filled_before_a_duplicate_is_skipped(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        first = tiny_jpeg(root, "a.jpg")
        _insert_without_hash(catalog, first)
        second = root / "b.jpg"
        second.write_bytes(first.read_bytes())
        self.assertEqual(import_originals(catalog, [second]), 0)
        self.assertIsNotNone(stored_hash(catalog, first))
        self.assertEqual(original_paths(catalog), [str(first)])

    def test_a_missing_original_does_not_block_the_next_import(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        _insert_without_hash(catalog, root / "gone.jpg")
        photo = tiny_jpeg(root, "a.jpg")
        self.assertFalse(is_duplicate(catalog, root / "gone.jpg"))
        self.assertEqual(import_originals(catalog, [photo]), 1)
        self.assertIsNone(stored_hash(catalog, root / "gone.jpg"))

    def test_an_older_photos_table_gains_a_hash_column(self) -> None:
        database = Path(tempfile.mkdtemp()) / "catalog.sqlite"
        _legacy_photos(database)
        apply_schema(database)
        self.assertIsNone(stored_hash(database, Path("/shoots/a.jpg")))

    def test_missing_file_is_skipped(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "wedding")
        missing = Path(tempfile.mkdtemp()) / "gone.jpg"
        self.assertEqual(import_originals(catalog, [missing]), 0)
        self.assertEqual(list_index_images(catalog), [])

    def test_unreadable_file_is_skipped(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        junk = root / "notes.txt"
        junk.write_text("not a photo", encoding="utf-8")
        self.assertEqual(import_originals(catalog, [junk]), 0)

    def test_raw_thumb_bytes_accept_jpeg_and_bitmap(self) -> None:
        jpeg = _thumb(rawpy.ThumbFormat.JPEG, b"\xff\xd8\xff")
        self.assertEqual(_thumb_bytes(jpeg), b"\xff\xd8\xff")
        bitmap = _thumb(rawpy.ThumbFormat.BITMAP, np.zeros((4, 4, 3), dtype=np.uint8))
        self.assertTrue(_thumb_bytes(bitmap).startswith(b"\xff\xd8"))

    def test_legacy_file_catalog_gets_a_preview_folder(self) -> None:
        from tests.test_catalog_package import legacy_catalog
        root = Path(tempfile.mkdtemp())
        catalog = legacy_catalog(root)
        photo = tiny_jpeg(root, "a.jpg")
        self.assertEqual(import_originals(catalog, [photo]), 1)
        self.assertEqual(len(list_index_images(catalog)), 1)
        self.assertTrue(Path(f"{catalog}.previews").is_dir())


class ImportDialogRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_add_records_the_open_catalog(self) -> None:
        from src.ui.dialogs.import_dialog import ImportDialog
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        dialog = ImportDialog()
        dialog.bind_catalog(catalog)
        dialog.selected_images = [tiny_jpeg(root, "a.jpg")]
        dialog._add_selection_to_catalog()
        self.assertEqual(len(list_index_images(catalog)), 1)
        copy = root / "b.jpg"
        copy.write_bytes(dialog.selected_images[0].read_bytes())
        self.assertTrue(dialog._skip_duplicate(copy))
        dialog.duplicate_box.setChecked(True)
        self.assertFalse(dialog._skip_duplicate(copy))
        dialog.close()
