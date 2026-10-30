import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.develop_settings import read_develop_settings, write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.index_images import list_index_images
from src.develop.crop_settings import CropSettings, crop_box, decode_crop, encode_crop, lock_edges
from src.develop.crop_store import load_crop, save_crop
from src.imaging.crop import crop_image
from src.importing.originals import import_originals
from src.ui.preview_image import crop_preview

APP = QApplication.instance() or QApplication([])
FRAMED = CropSettings(10, 20, 30, 5, 3, True)


def _catalog_with_photo() -> tuple[Path, Path]:
    folder = Path(tempfile.mkdtemp())
    original = folder / "frame.jpg"
    Image.new("RGB", (40, 20), "gray").save(original)
    catalog = create_catalog(folder / "shoot")
    import_originals(catalog, [original])
    return catalog, original


def _panel(catalog: Path):
    from src.ui.panels.develop_panel import DevelopPanel
    panel = DevelopPanel()
    panel.show_catalog(catalog)
    panel._cancel_load()
    return panel


def _slider(panel, title: str):
    return next(row for row in panel._controls.sliders if row.title == title)


class CropSettingsTests(unittest.TestCase):
    def test_empty_crop_is_empty(self) -> None:
        self.assertTrue(CropSettings().is_empty)

    def test_lock_alone_does_not_make_a_crop(self) -> None:
        self.assertTrue(CropSettings(locked=True).is_empty)

    def test_any_edge_or_angle_makes_a_crop(self) -> None:
        self.assertFalse(CropSettings(angle=2).is_empty)
        self.assertFalse(CropSettings(bottom=1).is_empty)

    def test_encode_always_writes_every_key(self) -> None:
        encoded = encode_crop(CropSettings())
        self.assertEqual(encoded["CropLeft"], "0")
        self.assertEqual(encoded["CropAspectLock"], "0")
        self.assertEqual(len(encoded), 6)

    def test_decode_round_trips_a_crop(self) -> None:
        self.assertEqual(decode_crop(encode_crop(FRAMED)), FRAMED)

    def test_decode_ignores_invalid_and_missing_values(self) -> None:
        decoded = decode_crop({"CropLeft": "x", "CropTop": "2.5", "CropRight": "7"})
        self.assertEqual(decoded, CropSettings(right=7))

    def test_box_of_empty_crop_is_the_whole_image(self) -> None:
        self.assertEqual(crop_box((40, 20), CropSettings()), (0, 0, 40, 20))

    def test_box_trims_percent_of_each_side(self) -> None:
        self.assertEqual(crop_box((100, 50), CropSettings(10, 20, 30, 10)), (10, 10, 70, 45))

    def test_box_is_never_smaller_than_one_pixel(self) -> None:
        left, top, right, bottom = crop_box((10, 10), CropSettings(90, 90, 90, 90))
        self.assertGreaterEqual(right - left, 1)
        self.assertGreaterEqual(bottom - top, 1)

    def test_box_stays_inside_the_image(self) -> None:
        self.assertEqual(crop_box((10, 10), CropSettings(95, 0, 0, 0))[0], 9)


class LockEdgesTests(unittest.TestCase):
    def test_unlocked_crop_is_left_alone(self) -> None:
        crop = CropSettings(left=10)
        self.assertIs(lock_edges(crop, "CropLeft"), crop)

    def test_horizontal_change_moves_the_bottom_edge(self) -> None:
        locked = lock_edges(CropSettings(left=10, right=10, locked=True), "CropLeft")
        self.assertEqual(locked.bottom, 20)

    def test_vertical_change_moves_the_right_edge(self) -> None:
        locked = lock_edges(CropSettings(top=5, bottom=5, locked=True), "CropTop")
        self.assertEqual(locked.right, 10)

    def test_locked_edge_stays_in_range(self) -> None:
        locked = lock_edges(CropSettings(top=40, bottom=80, locked=True), "CropBottom")
        self.assertEqual(locked.right, 90)
        self.assertEqual(lock_edges(CropSettings(left=0, top=30, locked=True), "CropLeft").bottom, 0)

    def test_lock_keeps_the_original_ratio(self) -> None:
        crop = lock_edges(CropSettings(left=10, right=10, locked=True), "CropLeft")
        left, top, right, bottom = crop_box((200, 100), crop)
        self.assertEqual((right - left) / (bottom - top), 2.0)


class CropImageTests(unittest.TestCase):
    def test_empty_crop_returns_the_same_image(self) -> None:
        image = Image.new("RGB", (40, 20))
        self.assertIs(crop_image(image, CropSettings()), image)

    def test_edges_shrink_the_image(self) -> None:
        self.assertEqual(crop_image(Image.new("RGB", (100, 50)), CropSettings(10, 20, 30, 10)).size, (60, 35))

    def test_angle_grows_the_canvas_before_cropping(self) -> None:
        rotated = crop_image(Image.new("RGB", (100, 50)), CropSettings(angle=10))
        self.assertGreater(rotated.width, 100)
        self.assertGreater(rotated.height, 50)

    def test_crop_does_not_change_the_source_image(self) -> None:
        image = Image.new("RGB", (100, 50))
        crop_image(image, CropSettings(10, 10, 10, 10, 5))
        self.assertEqual(image.size, (100, 50))


class CropPreviewTests(unittest.TestCase):
    def test_empty_crop_keeps_the_image(self) -> None:
        image = QImage(40, 20, QImage.Format.Format_RGB32)
        self.assertIs(crop_preview(image, CropSettings()), image)

    def test_null_image_is_returned(self) -> None:
        image = QImage()
        self.assertIs(crop_preview(image, FRAMED), image)

    def test_preview_matches_export_size(self) -> None:
        crop = CropSettings(10, 20, 30, 10)
        preview = crop_preview(QImage(100, 50, QImage.Format.Format_RGB32), crop)
        exported = crop_image(Image.new("RGB", (100, 50)), crop)
        self.assertEqual((preview.width(), preview.height()), exported.size)

    def test_angle_changes_the_canvas(self) -> None:
        preview = crop_preview(QImage(100, 50, QImage.Format.Format_RGB32), CropSettings(angle=10))
        self.assertGreater(preview.width(), 100)


class CropStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()

    def test_saved_crop_loads_again(self) -> None:
        save_crop(self.catalog, 1, FRAMED)
        self.assertEqual(load_crop(self.catalog, 1), FRAMED)

    def test_photo_without_crop_loads_empty(self) -> None:
        self.assertEqual(load_crop(self.catalog, 1), CropSettings())

    def test_save_keeps_other_settings(self) -> None:
        write_develop_settings(self.catalog, 1, {"Exposure": "4"})
        save_crop(self.catalog, 1, FRAMED)
        self.assertEqual(read_develop_settings(self.catalog, 1)["Exposure"], "4")

    def test_saving_leaves_the_original_unchanged(self) -> None:
        before = content_hash(self.original)
        save_crop(self.catalog, 1, FRAMED)
        self.assertEqual(content_hash(self.original), before)


class DevelopCropPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()
        self.panel = _panel(self.catalog)
        self.panel._show_photo(list_index_images(self.catalog)[0])

    def test_crop_slider_edits_the_preview_and_is_saved(self) -> None:
        full = self.panel.preview.pixmap().width()
        _slider(self.panel, "Left").set_value(40)
        self.panel._save_tone()
        self.assertEqual(load_crop(self.catalog, 1).left, 40)
        self.assertLessEqual(self.panel.preview.pixmap().width(), full)

    def test_crop_loads_when_the_photo_is_shown_again(self) -> None:
        save_crop(self.catalog, 1, FRAMED)
        self.panel._show_photo(list_index_images(self.catalog)[0])
        self.assertEqual(self.panel._crop.read(), FRAMED)

    def test_lock_keeps_both_states_visible_and_latest_crop_saved(self) -> None:
        self.panel._controls.crop_lock.setChecked(True)
        _slider(self.panel, "Left").set_value(10)
        self.assertEqual(_slider(self.panel, "Bottom").value(), 10)
        self.panel._controls.crop_lock.setChecked(False)
        _slider(self.panel, "Left").set_value(20)
        self.panel._save_tone()
        saved = load_crop(self.catalog, 1)
        self.assertEqual((saved.left, saved.bottom, saved.locked), (20, 10, False))

    def test_reset_returns_the_empty_crop(self) -> None:
        self.panel._controls.crop_lock.setChecked(True)
        _slider(self.panel, "Angle").set_value(7)
        self.panel._reset_controls()
        self.panel._save_tone()
        self.assertEqual(load_crop(self.catalog, 1), CropSettings())

    def test_photo_without_stored_crop_shows_the_empty_crop(self) -> None:
        _slider(self.panel, "Top").set_value(30)
        self.panel._save_tone()
        write_develop_settings(self.catalog, 1, {})
        self.panel._show_photo(list_index_images(self.catalog)[0])
        self.assertEqual(self.panel._crop.read(), CropSettings())

    def test_editing_a_crop_never_touches_the_original(self) -> None:
        before = content_hash(self.original)
        _slider(self.panel, "Right").set_value(30)
        self.panel._save_tone()
        self.assertEqual(content_hash(self.original), before)


if __name__ == "__main__":
    unittest.main()
