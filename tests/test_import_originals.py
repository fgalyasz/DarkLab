import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import rawpy
from PIL import Image

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.catalog.database import create_catalog, original_paths
from src.catalog.folders import imported_folders
from src.catalog.index_images import list_index_images, read_index_image
from src.importing.originals import _raw_thumb_bytes, import_originals


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


def tiny_jpeg(folder: Path, name: str) -> Path:
    path = folder / name
    Image.new("RGB", (8, 6), (20, 40, 60)).save(path, format="JPEG")
    return path


class ImportOriginalTests(unittest.TestCase):
    def test_import_writes_an_index_image(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "wedding")
        first = tiny_jpeg(root, "a.jpg")
        second = tiny_jpeg(root, "b.jpg")
        self.assertEqual(import_originals(catalog, [first, second, first]), 3)
        self.assertEqual(original_paths(catalog), [str(first), str(second)])
        self.assertEqual(imported_folders(catalog), [str(root)])
        indexes = list_index_images(catalog)
        self.assertEqual(len(indexes), 2)
        self.assertTrue(read_index_image(catalog, 1).startswith(b"\xff\xd8"))

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
        dialog.close()
