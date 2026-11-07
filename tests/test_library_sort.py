import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.file_hash import content_hash
from src.catalog.marks import write_mark
from src.catalog.capture_time import capture_time
from src.catalog.library_query import IMPORTED, NAME, RATING
from src.importing.originals import import_originals
from src.ui.panels.library_browser_panel import LibraryBrowserPanel

APP = QApplication.instance() or QApplication([])


def _original(folder: Path, name: str, shade: int, captured: str | None) -> Path:
    path = folder / name
    image = Image.new("RGB", (16, 16), (shade, shade, shade))
    exif = image.getexif()
    if captured is not None:
        exif.get_ifd(0x8769)[36867] = captured
    image.save(path, exif=exif)
    return path


def _ids(paths: list[Path]) -> list[int]:
    return [int(path.stem) for path in paths]


class CaptureTimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())

    def test_exif_capture_date_wins_over_the_file_date(self) -> None:
        early = _original(self.folder, "early.jpg", 10, "2001:01:01 00:00:00")
        late = _original(self.folder, "late.jpg", 20, "2002:01:01 00:00:00")
        self.assertLess(capture_time(early), capture_time(late))

    def test_file_without_exif_uses_the_file_date(self) -> None:
        plain = _original(self.folder, "plain.jpg", 10, None)
        self.assertEqual(capture_time(plain), plain.stat().st_mtime)

    def test_unreadable_capture_text_uses_the_file_date(self) -> None:
        odd = _original(self.folder, "odd.jpg", 10, "not a date")
        self.assertEqual(capture_time(odd), odd.stat().st_mtime)

    def test_unreadable_original_uses_the_file_date(self) -> None:
        plain = _original(self.folder, "plain.jpg", 10, "2001:01:01 00:00:00")
        with patch("src.catalog.capture_time.exifread.process_file", side_effect=OSError("denied")):
            self.assertEqual(capture_time(plain), plain.stat().st_mtime)

    def test_missing_original_has_no_capture_time(self) -> None:
        self.assertIsNone(capture_time(self.folder / "gone.jpg"))


class LibrarySortPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.originals = [
            _original(self.folder, "b.jpg", 30, "2020:01:03 10:00:00"),
            _original(self.folder, "c.jpg", 90, "2020:01:01 10:00:00"),
            _original(self.folder, "a.jpg", 150, "2020:01:02 10:00:00"),
        ]
        self.catalog = create_catalog(self.folder / "shoot")
        import_originals(self.catalog, self.originals)
        write_mark(self.catalog, 3, "rating", "5")
        write_mark(self.catalog, 1, "rating", "2")
        self.panel = LibraryBrowserPanel()
        self.panel.show_catalog(self.catalog)
        self.panel._cancel_load()

    def _choose(self, mode: str) -> list[int]:
        self.panel.sort_combo.setCurrentIndex(self.panel.sort_combo.findData(mode))
        return _ids(self.panel.grid.images)

    def test_combo_offers_the_four_sorts(self) -> None:
        texts = [self.panel.sort_combo.itemText(row) for row in range(self.panel.sort_combo.count())]
        self.assertEqual(texts, ["Capture Time", "File Name", "Import Time", "Rating"])

    def test_default_is_capture_time(self) -> None:
        self.assertEqual(_ids(self.panel.grid.images), [2, 3, 1])

    def test_each_sort_orders_the_grid(self) -> None:
        self.assertEqual(self._choose(NAME), [3, 1, 2])
        self.assertEqual(self._choose(IMPORTED), [1, 2, 3])
        self.assertEqual(self._choose(RATING), [3, 1, 2])

    def test_filmstrip_follows_the_grid(self) -> None:
        self._choose(NAME)
        self.assertEqual(self.panel.filmstrip.count(), 3)

    def test_sort_applies_after_the_filter(self) -> None:
        self.panel.rating_combo.setCurrentIndex(self.panel.rating_combo.findData("2"))
        self.assertEqual(self._choose(RATING), [3, 1])

    def test_sort_never_touches_originals(self) -> None:
        before = content_hash(self.originals[0])
        self._choose(RATING)
        self.assertEqual(content_hash(self.originals[0]), before)


if __name__ == "__main__":
    unittest.main()
