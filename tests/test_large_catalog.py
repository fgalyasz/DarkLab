import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication

from src.catalog.capture_time import fill_missing_capture_times
from src.catalog.catalog_folders import catalog_folders, folder_photo_ids
from src.catalog.database import create_catalog
from src.catalog.index_images import IndexPaths, index_image_path
from src.catalog.library_query import (
    CAPTURE, IMPORTED, NAME, RATING, MarkFilter, query_photo_ids,
)
from src.catalog.locations import database_file
from src.catalog.marks import read_marked, write_mark
from src.catalog.missing import missing_photo_ids
from src.catalog.optimize import optimize_catalog
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.widgets.filmstrip_widget import FilmstripWidget

APP = QApplication.instance() or QApplication([])
BIG_COUNT = 100_000
INSERT_PHOTO = "INSERT INTO photos (id, original_path, capture_time) VALUES (?, ?, ?)"
READ_CAPTURES = "SELECT id, capture_time FROM photos ORDER BY id"
PHOTOS = (
    (1, "/shoot/b.jpg", 30.0),
    (2, "/shoot/C.jpg", None),
    (3, "/other/a.jpg", 10.0),
    (4, "/shoot/d.jpg", 20.0),
)


def _catalog(rows: tuple[tuple[int, str, float | None], ...]) -> Path:
    catalog = create_catalog(Path(tempfile.mkdtemp()) / "shoot")
    connection = sqlite3.connect(database_file(catalog))
    with connection:
        connection.executemany(INSERT_PHOTO, rows)
    connection.close()
    return catalog


def _big_catalog() -> Path:
    return _catalog(tuple((i, f"/shoot/{i // 500}/IMG_{i}.jpg", float(i)) for i in range(1, BIG_COUNT + 1)))


def _panel(catalog: Path) -> LibraryBrowserPanel:
    panel = LibraryBrowserPanel()
    panel.show_catalog(catalog)
    panel._pool.setMaxThreadCount(0)
    return panel


class LibraryQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = _catalog(PHOTOS)
        write_mark(self.catalog, 1, "rating", "4")
        write_mark(self.catalog, 3, "rating", "5")
        write_mark(self.catalog, 3, "pick", "accepted")
        write_mark(self.catalog, 4, "color", "red")

    def _ids(self, mode: str = IMPORTED, marks: MarkFilter | None = None, scope=None) -> list[int]:
        return query_photo_ids(self.catalog, marks or MarkFilter(), mode, scope)

    def test_capture_time_sorts_oldest_first_and_unknown_last(self) -> None:
        self.assertEqual(self._ids(CAPTURE), [3, 4, 1, 2])

    def test_file_name_sorts_case_insensitively(self) -> None:
        self.assertEqual(self._ids(NAME), [3, 1, 2, 4])

    def test_import_time_follows_photo_ids(self) -> None:
        self.assertEqual(self._ids(IMPORTED), [1, 2, 3, 4])

    def test_rating_is_best_first_and_ties_keep_import_order(self) -> None:
        self.assertEqual(self._ids(RATING), [3, 1, 2, 4])

    def test_rating_filter_keeps_photos_at_or_above_the_minimum(self) -> None:
        self.assertEqual(self._ids(marks=MarkFilter(minimum_rating="5")), [3])
        self.assertEqual(self._ids(marks=MarkFilter(minimum_rating="4")), [1, 3])

    def test_unreadable_minimum_rating_keeps_every_photo(self) -> None:
        self.assertEqual(self._ids(marks=MarkFilter(minimum_rating="x")), [1, 2, 3, 4])

    def test_pick_and_color_filters_combine(self) -> None:
        self.assertEqual(self._ids(marks=MarkFilter(pick="accepted")), [3])
        self.assertEqual(self._ids(marks=MarkFilter(pick="none")), [1, 2, 4])
        self.assertEqual(self._ids(marks=MarkFilter(pick="none", color="red")), [4])
        self.assertEqual(self._ids(marks=MarkFilter(color="none")), [1, 2, 3])

    def test_scope_limits_the_result_and_keeps_the_order(self) -> None:
        self.assertEqual(self._ids(NAME, scope=frozenset({4, 1})), [1, 4])

    def test_unknown_sort_mode_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self._ids("size")

    def test_damaged_catalog_logs_and_lists_nothing(self) -> None:
        database_file(self.catalog).write_bytes(b"torn" * 500)
        with self.assertLogs("src.catalog.library_query", level="WARNING"):
            self.assertEqual(self._ids(), [])


class CaptureTimeStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.original = self.folder / "a.jpg"
        self.original.write_bytes(b"not an image")
        self.catalog = _catalog(((1, str(self.original), None), (2, str(self.folder / "gone.jpg"), None)))

    def _stored(self) -> dict[int, float | None]:
        connection = sqlite3.connect(database_file(self.catalog))
        try:
            return {int(row[0]): row[1] for row in connection.execute(READ_CAPTURES)}
        finally:
            connection.close()

    def test_fill_stores_times_of_existing_originals_only(self) -> None:
        self.assertEqual(fill_missing_capture_times(self.catalog), 1)
        self.assertEqual(self._stored(), {1: self.original.stat().st_mtime, 2: None})

    def test_fill_keeps_times_that_are_already_stored(self) -> None:
        fill_missing_capture_times(self.catalog)
        self.assertEqual(fill_missing_capture_times(self.catalog), 0)

    def test_optimize_stores_capture_times(self) -> None:
        optimize_catalog(self.catalog)
        self.assertEqual(self._stored()[1], self.original.stat().st_mtime)


class MissingOriginalsTests(unittest.TestCase):
    def test_only_the_asked_photos_are_checked(self) -> None:
        folder = Path(tempfile.mkdtemp())
        present = folder / "here.jpg"
        present.write_bytes(b"x")
        catalog = _catalog(((1, str(present), None), (2, str(folder / "gone.jpg"), None), (3, "/nowhere/c.jpg", None)))
        self.assertEqual(missing_photo_ids(catalog, [1, 2]), {2})
        self.assertEqual(missing_photo_ids(catalog, []), set())

    def test_ids_are_checked_in_chunks(self) -> None:
        catalog = _catalog(tuple((i, f"/nowhere/{i}.jpg", None) for i in range(1, 1201)))
        self.assertEqual(missing_photo_ids(catalog, range(1, 1201)), set(range(1, 1201)))


class CatalogLookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = _catalog(PHOTOS)

    def test_folders_group_photos_by_directory(self) -> None:
        folders = {folder.path: folder.photo_ids for folder in catalog_folders(self.catalog)}
        self.assertEqual(folders, {Path("/other"): (3,), Path("/shoot"): (1, 2, 4)})

    def test_folder_photo_ids_list_one_directory(self) -> None:
        self.assertEqual(folder_photo_ids(self.catalog, Path("/shoot")), (1, 2, 4))
        self.assertEqual(folder_photo_ids(self.catalog, Path("/none")), ())

    def test_only_marked_photos_are_read_as_marked(self) -> None:
        write_mark(self.catalog, 2, "pick", "rejected")
        write_mark(self.catalog, 4, "rating", "0")
        self.assertEqual(list(read_marked(self.catalog)), [2])

    def test_index_paths_are_built_once_per_photo(self) -> None:
        paths = IndexPaths(self.catalog)
        self.assertEqual(paths.of(3), index_image_path(self.catalog, 3))
        self.assertIs(paths.of(3), paths.of(3))


class FilmstripModelTests(unittest.TestCase):
    def test_rows_follow_the_photo_list(self) -> None:
        strip = FilmstripWidget()
        strip.set_photos([Path("a.jpg"), Path("b.jpg")])
        strip.select_photo(Path("b.jpg"))
        self.assertEqual((strip.count(), strip.currentIndex().row()), (2, 1))

    def test_selecting_an_unknown_photo_changes_nothing(self) -> None:
        strip = FilmstripWidget()
        strip.set_photos([Path("a.jpg")])
        strip.select_photo(Path("zzz.jpg"))
        self.assertFalse(strip.currentIndex().isValid())

    def test_selection_emits_the_path(self) -> None:
        strip = FilmstripWidget()
        chosen: list[str] = []
        strip.photo_selected.connect(chosen.append)
        strip.set_photos([Path("a.jpg"), Path("b.jpg")])
        strip.select_photo(Path("a.jpg"))
        self.assertEqual(chosen, ["a.jpg"])

    def test_model_answers_text_icon_and_path_of_a_row(self) -> None:
        strip = FilmstripWidget()
        strip.set_photos([Path("/x/a.jpg")])
        strip.set_thumbnail(Path("/x/a.jpg"), QPixmap(8, 8))
        model = strip.model()
        index = model.index(0)
        self.assertEqual(index.data(), "a.jpg")
        self.assertFalse(index.data(1).isNull())
        self.assertEqual(index.data(0x0100), "/x/a.jpg")
        self.assertIsNone(model.data(index, 99))
        self.assertIsNone(model.data(model.index(5), 0))
        self.assertEqual(model.rowCount(index), 0)


class LargeCatalogPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = _big_catalog()

    def setUp(self) -> None:
        self.panel = _panel(self.catalog)
        self.addCleanup(self.panel.close)
        self.addCleanup(self.panel._cancel_load)

    def test_library_lists_every_photo_in_capture_order(self) -> None:
        self.assertEqual(len(self.panel.grid.images), BIG_COUNT)
        self.assertEqual(self.panel.grid.images[0], index_image_path(self.catalog, 1))

    def test_open_never_stats_the_originals(self) -> None:
        with patch.object(Path, "is_file", side_effect=AssertionError("original checked")):
            self.panel.show_catalog(self.catalog)
        self.assertEqual(self.panel.grid.missing_images, set())

    def test_open_never_reads_exif(self) -> None:
        with patch("src.catalog.capture_time.exifread.process_file", side_effect=AssertionError("EXIF read")):
            self.panel.show_catalog(self.catalog)

    def test_missing_check_covers_only_the_visible_photos(self) -> None:
        visible = [index_image_path(self.catalog, i) for i in (1, 2)]
        self.panel._check_missing(visible)
        self.assertEqual(self.panel.grid.missing_images, set(visible))
        self.assertEqual(len(self.panel._checked), 2)

    def test_missing_check_skips_photos_already_checked(self) -> None:
        visible = [index_image_path(self.catalog, 1)]
        self.panel._check_missing(visible)
        with patch("src.ui.panels.library_browser_panel.missing_photo_ids", side_effect=AssertionError("again")):
            self.panel._check_missing(visible)

    def test_panel_without_a_catalog_lists_nothing(self) -> None:
        self.panel.show_catalog(None)
        self.panel._check_missing([Path("1.jpg")])
        self.assertEqual((self.panel.grid.images, self.panel._catalog_markers()), ([], {}))
        self.assertEqual(self.panel._visible_images(), [])

    def test_flag_filter_lists_the_flagged_photos(self) -> None:
        write_mark(self.catalog, 7, "pick", "accepted")
        self.panel.show_catalog(self.catalog)
        self.panel.pick_combo.setCurrentIndex(self.panel.pick_combo.findData("accepted"))
        self.assertEqual(self.panel.grid.images, [index_image_path(self.catalog, 7)])

    def test_rating_filter_lists_the_rated_photos(self) -> None:
        write_mark(self.catalog, 9, "rating", "3")
        self.panel.show_catalog(self.catalog)
        self.panel.rating_combo.setCurrentIndex(self.panel.rating_combo.findData("3"))
        self.assertEqual(self.panel.grid.images, [index_image_path(self.catalog, 9)])

    def test_flag_filter_still_works_after_optimize(self) -> None:
        catalog = _catalog(((1, "/shoot/a.jpg", 1.0), (2, "/shoot/b.jpg", 2.0)))
        optimize_catalog(catalog)
        write_mark(catalog, 2, "pick", "accepted")
        panel = _panel(catalog)
        self.addCleanup(panel.close)
        panel.pick_combo.setCurrentIndex(panel.pick_combo.findData("accepted"))
        self.assertEqual(panel.grid.images, [index_image_path(catalog, 2)])


if __name__ == "__main__":
    unittest.main()
