import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.cull_filter import (
    filter_by_marks, matches_color, matches_marks, matches_pick, matches_rating,
)
from src.catalog.database import create_catalog
from src.catalog.marks import write_mark
from src.importing.originals import import_originals
from src.ui.contrast import (
    MINIMUM_BODY_CONTRAST, body_label_contrast, contrast_ratio, parse_rgb,
)
from src.ui.themes import StyleSheet

APP = QApplication.instance() or QApplication([])
FIRST = Path("first.jpg")
SECOND = Path("second.jpg")
THIRD = Path("third.jpg")
MARKERS = {
    FIRST: {"rating": "5", "pick": "accepted", "color": "red"},
    SECOND: {"rating": "2", "pick": "rejected", "color": "none"},
}
SHADES = (30, 90, 150, 210)


class CullFilterDomainTests(unittest.TestCase):
    def test_rating_threshold(self) -> None:
        self.assertTrue(matches_rating("4", "3"))
        self.assertFalse(matches_rating("2", "3"))
        self.assertTrue(matches_rating("0", "any"))
        self.assertFalse(matches_rating("x", "1"))

    def test_pick_and_color_match_exactly(self) -> None:
        self.assertTrue(matches_pick("accepted", "accepted"))
        self.assertFalse(matches_pick("none", "accepted"))
        self.assertTrue(matches_pick("rejected", "any"))
        self.assertTrue(matches_color("red", "red"))
        self.assertFalse(matches_color("red", "blue"))
        self.assertTrue(matches_color("none", "any"))

    def test_marks_must_satisfy_every_filter(self) -> None:
        marks = MARKERS[FIRST]
        self.assertTrue(matches_marks(marks, "5", "accepted", "red"))
        self.assertFalse(matches_marks(marks, "5", "accepted", "blue"))
        self.assertFalse(matches_marks(marks, "5", "rejected", "red"))

    def test_no_filter_keeps_every_path(self) -> None:
        paths = [FIRST, SECOND, THIRD]
        self.assertEqual(filter_by_marks(paths, MARKERS), paths)

    def test_pick_filter_keeps_only_picked_paths(self) -> None:
        paths = [FIRST, SECOND, THIRD]
        self.assertEqual(filter_by_marks(paths, MARKERS, pick="accepted"), [FIRST])

    def test_path_without_marks_counts_as_unflagged(self) -> None:
        paths = [FIRST, SECOND, THIRD]
        self.assertEqual(filter_by_marks(paths, MARKERS, pick="none"), [THIRD])
        self.assertEqual(filter_by_marks(paths, MARKERS, minimum_rating="1"), [FIRST, SECOND])

    def test_color_filter_keeps_only_that_label(self) -> None:
        paths = [FIRST, SECOND, THIRD]
        self.assertEqual(filter_by_marks(paths, MARKERS, color="red"), [FIRST])


class CullFilterPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = Path(tempfile.mkdtemp())
        originals = [self._original(folder, shade) for shade in SHADES]
        self.catalog = create_catalog(folder / "shoot")
        import_originals(self.catalog, originals)
        write_mark(self.catalog, 1, "pick", "accepted")
        write_mark(self.catalog, 2, "pick", "accepted")
        write_mark(self.catalog, 3, "pick", "rejected")
        write_mark(self.catalog, 2, "color", "green")
        write_mark(self.catalog, 4, "rating", "4")
        self.panel = self._library()

    def _original(self, folder: Path, shade: int) -> Path:
        path = folder / f"frame_{shade}.jpg"
        Image.new("RGB", (16, 16), (shade, shade, shade)).save(path)
        return path

    def _library(self):
        from src.ui.panels.library_browser_panel import LibraryBrowserPanel
        panel = LibraryBrowserPanel()
        panel.show_catalog(self.catalog)
        panel._cancel_load()
        return panel

    def _choose(self, combo, value: str) -> None:
        combo.setCurrentIndex(combo.findData(value))

    def test_pick_filter_count_equals_pick_count(self) -> None:
        self._choose(self.panel.pick_combo, "accepted")
        self.assertEqual(len(self.panel.grid.images), 2)

    def test_clearing_returns_the_catalog_count(self) -> None:
        self._choose(self.panel.pick_combo, "rejected")
        self.assertEqual(len(self.panel.grid.images), 1)
        self.panel._clear_filter()
        self.assertEqual(len(self.panel.grid.images), len(SHADES))
        self.assertEqual(self.panel.pick_combo.currentData(), "any")
        self.assertEqual(self.panel.filter_edit.text(), "")

    def test_filters_combine(self) -> None:
        self._choose(self.panel.pick_combo, "accepted")
        self._choose(self.panel.color_combo, "green")
        self.assertEqual(len(self.panel.grid.images), 1)

    def test_rating_filter_still_applies(self) -> None:
        self._choose(self.panel.rating_combo, "4")
        self.assertEqual(len(self.panel.grid.images), 1)

    def test_status_shows_filtered_count(self) -> None:
        self._choose(self.panel.pick_combo, "none")
        self.assertEqual(self.panel.status_label.text(), "1 photos")


class DarkThemeContrastTests(unittest.TestCase):
    def test_black_on_white_is_maximal(self) -> None:
        self.assertAlmostEqual(contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0)

    def test_body_labels_meet_the_minimum(self) -> None:
        for sheet in (StyleSheet.LIGHTROOM, StyleSheet.IMPORT_DIALOG):
            self.assertGreaterEqual(body_label_contrast(sheet), MINIMUM_BODY_CONTRAST)

    def test_low_contrast_is_detected(self) -> None:
        sheet = "QWidget { background-color: rgb(49, 49, 49); } QLabel { color: rgb(70, 70, 70); }"
        self.assertLess(body_label_contrast(sheet), MINIMUM_BODY_CONTRAST)

    def test_missing_rule_or_color_is_an_error(self) -> None:
        with self.assertRaises(ValueError):
            parse_rgb("red")
        with self.assertRaises(ValueError):
            body_label_contrast("QLabel { color: rgb(1, 1, 1); }")
        with self.assertRaises(ValueError):
            body_label_contrast("QWidget { background-color: rgb(1, 1, 1); } QLabel { margin: 0; }")


if __name__ == "__main__":
    unittest.main()
