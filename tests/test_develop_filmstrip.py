import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.index_images import list_index_images
from src.importing.originals import import_originals

APP = QApplication.instance() or QApplication([])


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


if __name__ == "__main__":
    unittest.main()
