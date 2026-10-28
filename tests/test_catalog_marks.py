import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.database import apply_schema, create_catalog
from src.catalog.file_hash import content_hash
from src.catalog.index_images import index_image_path, list_index_images
from src.catalog.locations import database_file
from src.catalog.marks import read_marks, read_photo_marks, write_mark
from src.catalog.removal import remove_catalog_photo
from src.develop.mark_text import marks_text
from src.importing.originals import import_originals

APP = QApplication.instance() or QApplication([])
NO_MARKS = {"rating": "0", "pick": "none", "color": "none"}
OLD_PHOTO_TABLE = "CREATE TABLE photos (id INTEGER PRIMARY KEY, original_path TEXT, content_hash TEXT)"
WRITE_ERROR = "src.ui.panels.library_browser_panel.write_mark"


def _catalog_with_photo() -> tuple[Path, Path]:
    folder = Path(tempfile.mkdtemp())
    original = folder / "frame.jpg"
    Image.new("RGB", (16, 16), "gray").save(original)
    catalog = create_catalog(folder / "shoot")
    import_originals(catalog, [original])
    return catalog, original


def _library(catalog: Path):
    from src.ui.panels.library_browser_panel import LibraryBrowserPanel
    panel = LibraryBrowserPanel()
    panel.show_catalog(catalog)
    panel._cancel_load()
    return panel


def _develop(catalog: Path):
    from src.ui.panels.develop_panel import DevelopPanel
    panel = DevelopPanel()
    panel.show_catalog(catalog)
    panel._cancel_load()
    return panel


class MarksStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()

    def test_new_photo_has_no_marks(self) -> None:
        self.assertEqual(read_photo_marks(self.catalog, 1), NO_MARKS)

    def test_marks_round_trip(self) -> None:
        write_mark(self.catalog, 1, "rating", "4")
        write_mark(self.catalog, 1, "pick", "accepted")
        write_mark(self.catalog, 1, "color", "red")
        expected = {"rating": "4", "pick": "accepted", "color": "red"}
        self.assertEqual(read_photo_marks(self.catalog, 1), expected)
        self.assertEqual(read_marks(self.catalog), {1: expected})

    def test_unknown_photo_has_no_marks(self) -> None:
        self.assertEqual(read_photo_marks(self.catalog, 99), NO_MARKS)

    def test_bad_value_is_rejected_and_nothing_is_stored(self) -> None:
        with self.assertRaises(ValueError):
            write_mark(self.catalog, 1, "rating", "6")
        with self.assertRaises(ValueError):
            write_mark(self.catalog, 1, "pick", "maybe")
        self.assertEqual(read_photo_marks(self.catalog, 1), NO_MARKS)

    def test_unknown_mark_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            write_mark(self.catalog, 1, "id", "1")

    def test_marks_leave_the_original_unchanged(self) -> None:
        before = content_hash(self.original)
        write_mark(self.catalog, 1, "rating", "5")
        self.assertEqual(content_hash(self.original), before)

    def test_removing_a_photo_removes_its_marks(self) -> None:
        write_mark(self.catalog, 1, "rating", "5")
        remove_catalog_photo(self.catalog, 1, False)
        self.assertEqual(read_marks(self.catalog), {})

    def test_older_catalog_gains_the_mark_columns(self) -> None:
        old = Path(tempfile.mkdtemp()) / "old.sqlite"
        connection = sqlite3.connect(old)
        connection.execute(OLD_PHOTO_TABLE)
        connection.execute("INSERT INTO photos (original_path) VALUES ('a.jpg')")
        connection.commit()
        connection.close()
        apply_schema(old)
        self.assertEqual(read_marks(old), {1: NO_MARKS})

    def test_marks_survive_reopening_the_database(self) -> None:
        write_mark(self.catalog, 1, "color", "blue")
        self.assertTrue(database_file(self.catalog).is_file())
        self.assertEqual(read_photo_marks(self.catalog, 1)["color"], "blue")


class LibraryMarksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()
        self.index = list_index_images(self.catalog)[0]

    def test_grid_change_is_stored_in_the_catalog(self) -> None:
        panel = _library(self.catalog)
        panel.grid.selected_images = [self.index]
        panel.grid._set_marker_for_selected("rating", "3")
        panel.grid._set_marker_for_selected("pick", "rejected")
        self.assertEqual(read_photo_marks(self.catalog, 1)["rating"], "3")
        self.assertEqual(read_photo_marks(self.catalog, 1)["pick"], "rejected")

    def test_marks_return_after_restart(self) -> None:
        write_mark(self.catalog, 1, "rating", "2")
        write_mark(self.catalog, 1, "color", "green")
        panel = _library(self.catalog)
        self.assertEqual(panel.grid.image_markers[self.index]["rating"], "2")
        self.assertEqual(panel.grid.image_markers[self.index]["color"], "green")

    def test_other_photos_show_no_marks(self) -> None:
        panel = _library(self.catalog)
        self.assertEqual(panel.grid.image_markers[self.index], NO_MARKS)

    def test_no_catalog_has_no_markers(self) -> None:
        panel = _library(self.catalog)
        panel.show_catalog(None)
        self.assertEqual(panel.grid.image_markers, {})

    def test_change_without_a_catalog_is_ignored(self) -> None:
        panel = _library(self.catalog)
        panel.show_catalog(None)
        panel._on_marker_changed(self.index, "rating", "5")
        self.assertEqual(read_photo_marks(self.catalog, 1), NO_MARKS)

    def test_change_for_a_file_outside_the_catalog_is_ignored(self) -> None:
        panel = _library(self.catalog)
        panel._on_marker_changed(self.original, "rating", "5")
        self.assertEqual(read_photo_marks(self.catalog, 1), NO_MARKS)

    def test_failed_save_is_logged_and_not_raised(self) -> None:
        panel = _library(self.catalog)
        with patch(WRITE_ERROR, side_effect=sqlite3.OperationalError("locked")):
            with self.assertLogs("src.ui.panels.library_browser_panel", level="ERROR") as logged:
                panel._on_marker_changed(self.index, "rating", "5")
        self.assertIn("locked", logged.output[0])

    def test_invalid_value_is_logged_and_not_stored(self) -> None:
        panel = _library(self.catalog)
        with self.assertLogs("src.ui.panels.library_browser_panel", level="ERROR"):
            panel._on_marker_changed(self.index, "rating", "9")
        self.assertEqual(read_photo_marks(self.catalog, 1), NO_MARKS)


class DevelopMarksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()
        self.index = index_image_path(self.catalog, 1)

    def test_develop_shows_the_marks_set_in_library(self) -> None:
        library = _library(self.catalog)
        library._on_marker_changed(self.index, "rating", "3")
        library._on_marker_changed(self.index, "pick", "accepted")
        library._on_marker_changed(self.index, "color", "red")
        develop = _develop(self.catalog)
        develop._show_photo(self.index)
        self.assertEqual(develop.marks_label.text(), "★★★☆☆   Pick   Red")

    def test_develop_shows_empty_stars_without_marks(self) -> None:
        develop = _develop(self.catalog)
        develop._show_photo(self.index)
        self.assertEqual(develop.marks_label.text(), "☆☆☆☆☆")

    def test_develop_clears_marks_for_a_file_outside_the_catalog(self) -> None:
        develop = _develop(self.catalog)
        develop._show_photo(self.original)
        self.assertEqual(develop.marks_label.text(), "")

    def test_showing_develop_refreshes_the_marks(self) -> None:
        develop = _develop(self.catalog)
        develop._show_photo(self.index)
        write_mark(self.catalog, 1, "rating", "5")
        develop.show()
        self.assertEqual(develop.marks_label.text(), "★★★★★")

    def test_marks_without_a_catalog_are_blank(self) -> None:
        develop = _develop(self.catalog)
        develop._show_photo(self.index)
        develop.show_catalog(None)
        develop._show_marks()
        self.assertEqual(develop.marks_label.text(), "")


class MarksTextTests(unittest.TestCase):
    def test_rejected_flag_is_named(self) -> None:
        self.assertEqual(marks_text({"rating": "1", "pick": "rejected", "color": "none"}), "★☆☆☆☆   Rejected")

    def test_missing_keys_use_defaults(self) -> None:
        self.assertEqual(marks_text({}), "☆☆☆☆☆")


if __name__ == "__main__":
    unittest.main()
