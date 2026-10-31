import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.file_hash import content_hash
from src.catalog.index_images import list_index_images
from src.develop.tone_store import load_tone
from src.imaging.clipping import (
    HIGHLIGHT_COLOR, SHADOW_COLOR, clipping_color, is_highlight_clipped, is_shadow_clipped,
)
from src.importing.originals import import_originals
from src.ui.preview_image import clipping_overlay
from src.ui.widgets.histogram_widget import bins_from_image

APP = QApplication.instance() or QApplication([])


def _pixel(image: QImage, x: int = 0, y: int = 0) -> tuple[int, int, int]:
    color = image.pixelColor(x, y)
    return color.red(), color.green(), color.blue()


def _catalog_with_photo(color: tuple[int, int, int]) -> tuple[Path, Path]:
    folder = Path(tempfile.mkdtemp())
    original = folder / "frame.jpg"
    Image.new("RGB", (40, 20), color).save(original)
    catalog = create_catalog(folder / "shoot")
    import_originals(catalog, [original])
    return catalog, original


def _panel(catalog: Path):
    from src.ui.panels.develop_panel import DevelopPanel
    panel = DevelopPanel()
    panel.show_catalog(catalog)
    panel._cancel_load()
    panel._show_photo(list_index_images(catalog)[0])
    return panel


def _slider(panel, title: str):
    return next(row for row in panel._controls.sliders if row.title == title)


class ClippingColorTests(unittest.TestCase):
    def test_a_channel_at_the_top_is_a_clipped_highlight(self) -> None:
        self.assertTrue(is_highlight_clipped(255, 10, 10))
        self.assertFalse(is_highlight_clipped(254, 254, 254))

    def test_a_channel_at_the_bottom_is_a_clipped_shadow(self) -> None:
        self.assertTrue(is_shadow_clipped(10, 0, 10))
        self.assertFalse(is_shadow_clipped(1, 1, 1))

    def test_highlight_is_red_and_shadow_is_blue(self) -> None:
        self.assertEqual(clipping_color(255, 100, 100), HIGHLIGHT_COLOR)
        self.assertEqual(clipping_color(0, 100, 100), SHADOW_COLOR)

    def test_highlight_wins_when_a_pixel_is_both(self) -> None:
        self.assertEqual(clipping_color(255, 0, 100), HIGHLIGHT_COLOR)

    def test_a_midtone_is_not_clipped(self) -> None:
        self.assertIsNone(clipping_color(120, 120, 120))


class ClippingOverlayImageTests(unittest.TestCase):
    def _image(self) -> QImage:
        image = QImage(3, 1, QImage.Format.Format_RGB32)
        image.setPixelColor(0, 0, QColor(255, 255, 255))
        image.setPixelColor(1, 0, QColor(0, 0, 0))
        image.setPixelColor(2, 0, QColor(120, 120, 120))
        return image

    def test_clipped_pixels_are_painted_and_midtones_are_kept(self) -> None:
        result = clipping_overlay(self._image())
        self.assertEqual(_pixel(result, 0), HIGHLIGHT_COLOR)
        self.assertEqual(_pixel(result, 1), SHADOW_COLOR)
        self.assertEqual(_pixel(result, 2), (120, 120, 120))

    def test_the_source_image_is_not_changed(self) -> None:
        source = self._image()
        clipping_overlay(source)
        self.assertEqual(_pixel(source, 0), (255, 255, 255))

    def test_a_null_image_is_returned_as_it_is(self) -> None:
        self.assertTrue(clipping_overlay(QImage()).isNull())


class ClippingTogglePanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo((255, 255, 255))
        self.panel = _panel(self.catalog)

    def _preview_pixel(self) -> tuple[int, int, int]:
        return _pixel(self.panel.preview.pixmap().toImage())

    def test_clipping_starts_off(self) -> None:
        self.assertFalse(self.panel.clipping_button.isChecked())
        self.assertNotEqual(self._preview_pixel(), HIGHLIGHT_COLOR)

    def test_toggle_on_paints_clipped_pixels_and_off_removes_them(self) -> None:
        self.panel.clipping_button.setChecked(True)
        self.assertEqual(self._preview_pixel(), HIGHLIGHT_COLOR)
        self.panel.clipping_button.setChecked(False)
        self.assertNotEqual(self._preview_pixel(), HIGHLIGHT_COLOR)

    def test_toggle_writes_no_step_and_no_settings(self) -> None:
        steps = self.panel.history_widget.count()
        before = load_tone(self.catalog, 1)
        values = self.panel._controls.values()
        self.panel.clipping_button.setChecked(True)
        self.panel.clipping_button.setChecked(False)
        self.assertEqual(self.panel.history_widget.count(), steps)
        self.assertEqual(load_tone(self.catalog, 1), before)
        self.assertEqual(self.panel._controls.values(), values)

    def test_toggle_keeps_the_histogram_free_of_the_overlay(self) -> None:
        expected = bins_from_image(self.panel._source_image)
        self.panel.clipping_button.setChecked(True)
        self.assertEqual(self.panel.histogram._bins, expected)

    def test_toggle_never_touches_the_original(self) -> None:
        before = content_hash(self.original)
        self.panel.clipping_button.setChecked(True)
        self.assertEqual(content_hash(self.original), before)

    def test_overlay_follows_an_exposure_change(self) -> None:
        catalog, _ = _catalog_with_photo((100, 100, 100))
        panel = _panel(catalog)
        panel.clipping_button.setChecked(True)
        self.assertEqual(_pixel(panel.preview.pixmap().toImage()), (100, 100, 100))
        _slider(panel, "Exposure").set_value(100)
        self.assertEqual(_pixel(panel.preview.pixmap().toImage()), HIGHLIGHT_COLOR)


class HistogramFollowsExposureTests(unittest.TestCase):
    def test_exposure_change_moves_the_histogram(self) -> None:
        catalog, _ = _catalog_with_photo((100, 100, 100))
        panel = _panel(catalog)
        before = [list(channel) for channel in panel.histogram._bins]
        _slider(panel, "Exposure").set_value(50)
        self.assertNotEqual(panel.histogram._bins, tuple(before))

    def test_histogram_comes_from_the_shown_preview(self) -> None:
        catalog, _ = _catalog_with_photo((100, 100, 100))
        panel = _panel(catalog)
        _slider(panel, "Exposure").set_value(50)
        self.assertEqual(panel.histogram._bins, bins_from_image(panel._edited_image()))


if __name__ == "__main__":
    unittest.main()
