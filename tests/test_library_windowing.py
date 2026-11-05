import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QScrollArea

from src.catalog.database import create_catalog
from src.catalog.index_images import index_image_path
from src.catalog.locations import database_file
from src.catalog.photo_pages import iter_photo_id_pages, list_catalog_indexes
from src.imaging.lru_cache import LruCache
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.widgets.filmstrip_widget import FilmstripWidget
from src.ui.widgets.grid_image_widget import GridImageWidget

APP = QApplication.instance() or QApplication([])
PHOTO_COUNT = 10_000
INSERT_PHOTO = "INSERT INTO photos (id, original_path) VALUES (?, ?)"
LISTING = "src.catalog.index_images.list_index_images"


def _catalog_with(count: int) -> Path:
    catalog = create_catalog(Path(tempfile.mkdtemp()) / "big")
    connection = sqlite3.connect(database_file(catalog))
    with connection:
        connection.executemany(INSERT_PHOTO, [(i, f"/shoot/{i}.jpg") for i in range(1, count + 1)])
    connection.close()
    return catalog


def _grid(count: int) -> GridImageWidget:
    grid = GridImageWidget()
    grid.set_grid_layout(5, 100, 100, 0, 0, 0)
    grid.set_images([Path(f"{i}.jpg") for i in range(count)])
    return grid


def _image() -> QImage:
    image = QImage(4, 4, QImage.Format.Format_RGB32)
    image.fill(0)
    return image


class LruCacheTests(unittest.TestCase):

    def test_evicts_the_least_recently_used_key(self) -> None:
        cache: LruCache[str, int] = LruCache(2)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.get("a")
        self.assertEqual(cache.put("c", 3), ["b"])
        self.assertEqual(cache.keys(), ["a", "c"])

    def test_put_below_capacity_evicts_nothing(self) -> None:
        cache: LruCache[str, int] = LruCache(2)
        self.assertEqual(cache.put("a", 1), [])
        self.assertEqual((len(cache), "a" in cache, cache.capacity), (1, True, 2))

    def test_replacing_a_key_keeps_one_entry(self) -> None:
        cache: LruCache[str, int] = LruCache(1)
        cache.put("a", 1)
        self.assertEqual(cache.put("a", 2), [])
        self.assertEqual(cache.get("a"), 2)

    def test_missing_key_reads_as_none_and_clear_empties(self) -> None:
        cache: LruCache[str, int] = LruCache(1)
        self.assertIsNone(cache.get("a"))
        cache.put("a", 1)
        cache.clear()
        self.assertEqual(len(cache), 0)

    def test_rejects_a_capacity_below_one(self) -> None:
        with self.assertRaises(ValueError):
            LruCache(0)


class PhotoPageTests(unittest.TestCase):

    def test_pages_cover_every_photo_once_in_id_order(self) -> None:
        catalog = _catalog_with(25)
        pages = list(iter_photo_id_pages(catalog, 10))
        self.assertEqual([len(page) for page in pages], [10, 10, 5])
        self.assertEqual([i for page in pages for i in page], list(range(1, 26)))

    def test_indexes_come_from_sqlite_without_listing_previews(self) -> None:
        catalog = _catalog_with(3)
        with patch(LISTING, side_effect=AssertionError("directory listed")):
            indexes = list_catalog_indexes(catalog)
        self.assertEqual(indexes, [index_image_path(catalog, i) for i in (1, 2, 3)])

    def test_stray_preview_files_are_not_photos(self) -> None:
        catalog = _catalog_with(1)
        stray = index_image_path(catalog, 99)
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_bytes(b"jpeg")
        self.assertEqual(list_catalog_indexes(catalog), [index_image_path(catalog, 1)])

    def test_missing_catalog_has_no_pages(self) -> None:
        self.assertEqual(list(iter_photo_id_pages(Path(tempfile.mkdtemp()) / "none.darklab")), [])

    def test_damaged_catalog_logs_and_lists_nothing(self) -> None:
        folder = Path(tempfile.mkdtemp())
        broken = folder / "broken.sqlite"
        broken.write_bytes(b"not a database at all")
        with self.assertLogs("src.catalog.photo_pages", level="WARNING"):
            self.assertEqual(list_catalog_indexes(broken), [])

    def test_rejects_a_page_size_below_one(self) -> None:
        with self.assertRaises(ValueError):
            list(iter_photo_id_pages(_catalog_with(1), 0))


class GridWindowTests(unittest.TestCase):

    def test_range_covers_only_the_rows_in_view(self) -> None:
        grid = _grid(1000)
        self.assertEqual(grid.index_range(0, 150), range(0, 10))
        self.assertEqual(grid.index_range(1000, 1050), range(50, 55))

    def test_range_is_clamped_to_the_photo_count(self) -> None:
        grid = _grid(12)
        self.assertEqual(grid.index_range(-500, 100000), range(0, 12))
        self.assertEqual(grid.index_range(5000, 6000), range(12, 12))

    def test_unshown_grid_requests_nothing(self) -> None:
        grid = _grid(50)
        requests: list = []
        grid.thumbnails_needed.connect(requests.append)
        grid.request_visible_thumbnails()
        self.assertEqual(requests, [])

    def test_shown_grid_requests_only_missing_visible_thumbnails(self) -> None:
        grid = _grid(1000)
        scroll = QScrollArea()
        scroll.setWidget(grid)
        scroll.resize(520, 300)
        scroll.show()
        grid.set_thumbnail(Path("0.jpg"), QPixmap(4, 4))
        requests: list = []
        grid.thumbnails_needed.connect(requests.append)
        grid.request_visible_thumbnails()
        scroll.close()
        wanted = requests[0]
        self.assertNotIn(Path("0.jpg"), wanted)
        self.assertLess(len(wanted), 40)

    def test_cell_lookup_uses_the_position(self) -> None:
        grid = _grid(100)
        grid.set_grid_layout(5, 100, 100, 10, 0, 0)
        self.assertEqual(grid._get_index_at_pos(QPoint(115, 200)), 6)
        self.assertEqual(grid._get_index_at_pos(QPoint(105, 5)), -1)
        self.assertEqual(grid._get_index_at_pos(QPoint(-3, 5)), -1)
        self.assertEqual(grid._get_index_at_pos(QPoint(5, -5)), -1)
        self.assertEqual(grid._get_index_at_pos(QPoint(590, 5)), -1)

    def test_remove_thumbnail_drops_only_that_pixmap(self) -> None:
        grid = _grid(3)
        grid.set_thumbnail(Path("0.jpg"), QPixmap(4, 4))
        grid.set_thumbnail(Path("1.jpg"), QPixmap(4, 4))
        grid.remove_thumbnail(Path("0.jpg"))
        grid.remove_thumbnail(Path("2.jpg"))
        self.assertEqual(list(grid.thumbnails), [Path("1.jpg")])


class FilmstripCacheTests(unittest.TestCase):

    def test_thumbnail_can_be_cleared_again(self) -> None:
        strip = FilmstripWidget()
        strip.set_photos([Path("a.jpg"), Path("b.jpg")])
        strip.set_thumbnail(Path("a.jpg"), QPixmap(8, 8))
        self.assertFalse(strip.item(0).icon().isNull())
        strip.clear_thumbnail(Path("a.jpg"))
        strip.clear_thumbnail(Path("zzz.jpg"))
        self.assertTrue(strip.item(0).icon().isNull())

    def test_lookup_follows_the_current_photos(self) -> None:
        strip = FilmstripWidget()
        strip.set_photos([Path("a.jpg")])
        strip.set_photos([Path("b.jpg")])
        strip.set_thumbnail(Path("a.jpg"), QPixmap(8, 8))
        self.assertTrue(strip.item(0).icon().isNull())


class LibraryWindowTests(unittest.TestCase):

    def _panel(self, count: int) -> LibraryBrowserPanel:
        catalog = _catalog_with(count)
        panel = LibraryBrowserPanel()
        panel.show_catalog(catalog)
        panel._pool.setMaxThreadCount(0)
        self.addCleanup(panel.close)
        self.addCleanup(panel._cancel_load)
        return panel

    def test_opening_a_large_catalog_decodes_no_thumbnail(self) -> None:
        panel = self._panel(PHOTO_COUNT)
        self.assertEqual(len(panel.grid.images), PHOTO_COUNT)
        self.assertEqual(len(panel._relays), 0)
        self.assertEqual(len(panel._thumbs), 0)

    def test_requests_queue_each_path_once(self) -> None:
        panel = self._panel(10)
        paths = list(panel.grid.images[:3])
        panel._request_thumbs(paths)
        panel._request_thumbs(paths)
        self.assertEqual(len(panel._relays), 3)

    def test_scrolling_five_hundred_cells_keeps_the_cache_bounded(self) -> None:
        panel = self._panel(600)
        panel._thumbs = LruCache(50)
        for photo in panel.grid.images[:500]:
            panel._on_thumb(str(photo), _image(), panel._session)
        self.assertEqual(len(panel._thumbs), 50)
        self.assertEqual(len(panel.grid.thumbnails), 50)
        self.assertEqual(len(panel._requested), 0)

    def test_evicted_thumbnail_leaves_grid_and_filmstrip(self) -> None:
        panel = self._panel(3)
        panel._thumbs = LruCache(1)
        first, second = panel.grid.images[:2]
        panel._on_thumb(str(first), _image(), panel._session)
        panel._on_thumb(str(second), _image(), panel._session)
        self.assertNotIn(first, panel.grid.thumbnails)
        self.assertTrue(panel.filmstrip.item(0).icon().isNull())
        self.assertFalse(panel.filmstrip.item(1).icon().isNull())

    def test_evicted_thumbnail_can_be_requested_again(self) -> None:
        panel = self._panel(3)
        panel._thumbs = LruCache(1)
        first, second = panel.grid.images[:2]
        panel._request_thumbs([first])
        panel._on_thumb(str(first), _image(), panel._session)
        panel._on_thumb(str(second), _image(), panel._session)
        panel._request_thumbs([first])
        self.assertEqual(len(panel._relays), 2)

    def test_stale_or_empty_thumbnail_is_ignored(self) -> None:
        panel = self._panel(2)
        photo = str(panel.grid.images[0])
        panel._on_thumb(photo, _image(), panel._session - 1)
        panel._on_thumb(photo, QImage(), panel._session)
        self.assertEqual(len(panel._thumbs), 0)

    def test_cached_thumbnails_return_after_a_reload(self) -> None:
        panel = self._panel(3)
        photo = panel.grid.images[0]
        panel._on_thumb(str(photo), _image(), panel._session)
        panel._refresh_grid()
        self.assertIn(photo, panel.grid.thumbnails)
        panel._start_thumbs()
        panel._request_thumbs([photo])
        self.assertEqual(len(panel._relays), 0)

    def test_selected_photo_refreshes_the_navigator_when_its_thumbnail_lands(self) -> None:
        panel = self._panel(2)
        photo = panel.grid.images[0]
        panel._selected = [photo]
        panel._on_thumb(str(photo), _image(), panel._session)
        self.assertEqual(panel.meta_dimensions.text(), "4 x 4")

    def test_showing_a_missing_pixmap_changes_nothing(self) -> None:
        panel = self._panel(1)
        panel._show_thumb(panel.grid.images[0], None)
        self.assertEqual(panel.grid.thumbnails, {})

    def test_relay_is_released_once_its_result_arrives(self) -> None:
        panel = self._panel(2)
        photo = panel.grid.images[0]
        panel._request_thumbs([photo])
        relay = panel._relays[0]
        relay.receive(str(photo), photo.name, _image())
        self.assertEqual(len(panel._relays), 0)
        panel._release_relay(relay)


if __name__ == "__main__":
    unittest.main()
