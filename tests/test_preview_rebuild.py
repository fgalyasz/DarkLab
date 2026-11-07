import os
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.index_images import index_image_path, list_index_images
from src.catalog.locations import database_file, preview_directory
from src.catalog.photo_pages import list_catalog_indexes
from src.catalog.preview_index import missing_preview_ids
from src.importing.originals import import_originals
from src.importing.previews import RebuildReport, rebuild_previews
from src.ui.panels.library_browser_panel import LibraryBrowserPanel

APP = QApplication.instance() or QApplication([])
READ_HASHES = "SELECT id, content_hash FROM photos ORDER BY id"


def _original(folder: Path, name: str, shade: int) -> Path:
    path = folder / name
    Image.new("RGB", (16, 16), (shade, shade, shade)).save(path)
    return path


def _hashes(catalog: Path) -> list[tuple[int, str]]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        return [(int(row[0]), str(row[1])) for row in connection.execute(READ_HASHES).fetchall()]
    finally:
        connection.close()


class PreviewFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.originals = [_original(self.root, "a.jpg", 40), _original(self.root, "b.jpg", 200)]
        self.catalog = create_catalog(self.root / "shoot")
        import_originals(self.catalog, self.originals)

    def wipe_previews(self) -> None:
        shutil.rmtree(preview_directory(self.catalog))


class PreviewIndexTests(PreviewFixture):
    def test_wiped_previews_still_list_every_photo(self) -> None:
        expected = [index_image_path(self.catalog, 1), index_image_path(self.catalog, 2)]
        self.wipe_previews()
        self.assertEqual(list_index_images(self.catalog), [])
        self.assertEqual(list_catalog_indexes(self.catalog), expected)

    def test_missing_preview_ids_name_only_the_absent_files(self) -> None:
        self.assertEqual(missing_preview_ids(self.catalog), [])
        index_image_path(self.catalog, 2).unlink()
        self.assertEqual(missing_preview_ids(self.catalog), [2])

    def test_folder_without_a_database_has_no_photos(self) -> None:
        bare = self.root / "bare"
        bare.mkdir()
        self.assertEqual(list_catalog_indexes(bare), [])
        self.assertEqual(missing_preview_ids(bare), [])
        self.assertFalse(database_file(bare).exists())

    def test_unreadable_database_lists_nothing_from_rows(self) -> None:
        database_file(self.catalog).write_bytes(b"torn" * 500)
        self.assertEqual(missing_preview_ids(self.catalog), [])


class RebuildPreviewsTests(PreviewFixture):
    def test_rebuild_restores_every_preview_after_a_wipe(self) -> None:
        before = [path.read_bytes() for path in list_index_images(self.catalog)]
        self.wipe_previews()
        report = rebuild_previews(self.catalog)
        self.assertEqual(report, RebuildReport(rebuilt=2, unavailable=0))
        self.assertEqual([path.read_bytes() for path in list_index_images(self.catalog)], before)

    def test_rebuild_keeps_original_hashes_and_files(self) -> None:
        hashes = _hashes(self.catalog)
        data = [path.read_bytes() for path in self.originals]
        self.wipe_previews()
        rebuild_previews(self.catalog)
        self.assertEqual(_hashes(self.catalog), hashes)
        self.assertEqual([path.read_bytes() for path in self.originals], data)

    def test_rebuild_with_nothing_missing_changes_nothing(self) -> None:
        report = rebuild_previews(self.catalog)
        self.assertEqual(report, RebuildReport(rebuilt=0, unavailable=0))
        self.assertEqual(report.describe(), "All previews are present.")

    def test_missing_original_is_counted_and_others_are_rebuilt(self) -> None:
        self.wipe_previews()
        self.originals[0].unlink()
        report = rebuild_previews(self.catalog)
        self.assertEqual(report, RebuildReport(rebuilt=1, unavailable=1))
        self.assertIn("1 could not be rebuilt", report.describe())
        self.assertFalse(index_image_path(self.catalog, 1).exists())
        self.assertTrue(index_image_path(self.catalog, 2).is_file())

    def test_unreadable_original_is_counted(self) -> None:
        self.wipe_previews()
        self.originals[1].write_bytes(b"not an image")
        with patch("src.importing.previews.index_jpeg", side_effect=OSError("bad")):
            report = rebuild_previews(self.catalog)
        self.assertEqual(report.unavailable, 2)
        self.assertEqual(report.rebuilt, 0)

    def test_report_text_counts_rebuilt_previews(self) -> None:
        self.assertEqual(RebuildReport(2, 0).describe(), "Rebuilt 2 preview(s).")


class LibraryAfterWipeTests(PreviewFixture):
    def test_library_still_lists_photos_and_shows_them_after_rebuild(self) -> None:
        self.wipe_previews()
        panel = LibraryBrowserPanel()
        panel.show_catalog(self.catalog)
        panel._cancel_load()
        self.assertEqual(len(panel.grid.images), 2)
        rebuild_previews(self.catalog)
        panel.show_catalog(self.catalog)
        panel._cancel_load()
        self.assertTrue(all(Path(path).is_file() for path in panel.grid.images))


if __name__ == "__main__":
    unittest.main()
