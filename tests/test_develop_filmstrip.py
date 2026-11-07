import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.index_images import index_image_path, list_index_images
from src.catalog.locations import database_file
from src.imaging.lru_cache import LruCache
from src.importing.originals import import_originals

APP = QApplication.instance() or QApplication([])
BIG_COUNT = 10_000
INSERT_PHOTO = "INSERT INTO photos (id, original_path) VALUES (?, ?)"


def _catalog_with_photo() -> tuple[Path, Path]:
    folder = Path(tempfile.mkdtemp())
    original = folder / "frame.jpg"
    Image.new("RGB", (16, 16), "gray").save(original)
    catalog = create_catalog(folder / "shoot")
    import_originals(catalog, [original])
    return catalog, original


def _panel(catalog: Path):
    from src.ui.panels.develop_panel import DevelopPanel
    panel = DevelopPanel()
    panel.show_catalog(catalog)
    panel._cancel_load()
    return panel


def _big_catalog() -> Path:
    catalog = create_catalog(Path(tempfile.mkdtemp()) / "big")
    connection = sqlite3.connect(database_file(catalog))
    with connection:
        connection.executemany(INSERT_PHOTO, [(i, f"/shoot/{i}.jpg") for i in range(1, BIG_COUNT + 1)])
    connection.close()
    return catalog


def _idle_panel(catalog: Path):
    from src.ui.panels.develop_panel import DevelopPanel
    panel = DevelopPanel()
    panel._pool.setMaxThreadCount(0)
    panel.show_catalog(catalog)
    return panel


class DevelopFilmstripTests(unittest.TestCase):
    def test_filmstrip_lists_the_catalog_photos(self) -> None:
        catalog, _original = _catalog_with_photo()
        panel = _panel(catalog)
        self.assertEqual(panel._photos, list_index_images(catalog))
        self.assertEqual(panel.filmstrip.count(), 1)

    def test_filmstrip_follows_the_open_catalog(self) -> None:
        panel = _panel(_catalog_with_photo()[0])
        panel.show_catalog(None)
        self.assertEqual(panel.filmstrip.count(), 0)

    def test_filmstrip_ignores_folders_outside_the_catalog(self) -> None:
        panel = _panel(_catalog_with_photo()[0])
        self.assertFalse(hasattr(panel, "_load_folder"))
        self.assertFalse(hasattr(panel, "_discovery"))


class DevelopWindowedFilmstripTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = _big_catalog()

    def setUp(self) -> None:
        self.panel = _idle_panel(self.catalog)
        self.addCleanup(self.panel.close)
        self.addCleanup(self.panel._cancel_load)

    def test_every_photo_is_listed_but_only_nearby_cells_decode(self) -> None:
        self.assertEqual(self.panel.filmstrip.count(), BIG_COUNT)
        self.assertGreater(len(self.panel._requested), 0)
        self.assertLess(len(self.panel._requested), 100)
        self.assertEqual(len(self.panel._relays), len(self.panel._requested))

    def test_scrolling_requests_the_cells_that_come_into_view(self) -> None:
        strip = self.panel.filmstrip
        strip.resize(1000, 104)
        strip.doItemsLayout()
        strip.horizontalScrollBar().setValue(strip.horizontalScrollBar().maximum() // 2)
        self.assertTrue(any(int(path.stem) > BIG_COUNT // 4 for path in self.panel._requested))
        self.assertLess(len(self.panel._requested), 400)

    def test_requested_cells_are_not_requested_twice(self) -> None:
        before = len(self.panel._relays)
        self.panel._request_thumbs(list(self.panel._requested))
        self.assertEqual(len(self.panel._relays), before)

    def test_thumbnail_cache_is_bounded_and_evicts_from_the_strip(self) -> None:
        self.panel._thumbs = LruCache(1)
        first, second = self.panel._photos[:2]
        self.panel._on_thumb(str(first), _image(), self.panel._session)
        self.panel._on_thumb(str(second), _image(), self.panel._session)
        self.assertFalse(self.panel.filmstrip.has_thumbnail(first))
        self.assertTrue(self.panel.filmstrip.has_thumbnail(second))
        self.assertNotIn(first, self.panel._requested)

    def test_empty_catalog_requests_nothing(self) -> None:
        self.panel.show_catalog(None)
        self.assertEqual((len(self.panel._requested), self.panel.filmstrip.count()), (0, 0))

    def test_photos_come_from_the_catalog_rows_not_stray_previews(self) -> None:
        stray = index_image_path(self.catalog, BIG_COUNT + 5)
        stray.parent.mkdir(parents=True, exist_ok=True)
        stray.write_bytes(b"x")
        self.panel.show_catalog(self.catalog)
        self.assertNotIn(stray, self.panel._photos)


def _image() -> QImage:
    image = QImage(4, 4, QImage.Format.Format_RGB32)
    image.fill(0)
    return image


if __name__ == "__main__":
    unittest.main()
