import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PIL import Image
from PyQt6.QtGui import QColor, QImage
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.index_images import list_index_images
from src.develop.history import import_settings
from src.develop.tone_settings import encode_tone
from src.develop.white_balance import AS_SHOT, AUTO, CHOICES, CUSTOM, choice_for
from src.exporting.preset import ExportPreset
from src.exporting.render import render_photo
from src.importing.originals import import_originals
from src.imaging.color_grade import ColorGrade, apply_grade, auto_balance, channel_gains
from src.imaging.tone import grade_pil
from src.ui.preview_image import average_rgb, grade_image

APP = QApplication.instance() or QApplication([])
WARM_GRAY = (120, 100, 80)


def _slider(panel, title: str):
    return next(row for row in panel._controls.sliders if row.title == title)


def _pixels(color: tuple[int, int, int]) -> np.ndarray:
    return np.full((2, 2, 3), color, dtype=np.uint8)


def _panel_with_photo(color: tuple[int, int, int] = WARM_GRAY):
    from src.ui.panels.develop_panel import DevelopPanel
    folder = Path(tempfile.mkdtemp())
    original = folder / "frame.jpg"
    Image.new("RGB", (16, 16), color).save(original, quality=100)
    catalog = create_catalog(folder / "shoot")
    import_originals(catalog, [original])
    panel = DevelopPanel()
    panel.show_catalog(catalog)
    panel._cancel_load()
    panel._show_photo(list_index_images(catalog)[0])
    return panel, original


class ColorGradeTests(unittest.TestCase):
    def test_neutral_grade_returns_the_same_pixels(self) -> None:
        pixels = _pixels(WARM_GRAY)
        self.assertIs(apply_grade(pixels, ColorGrade()), pixels)

    def test_warmer_temperature_raises_red_and_lowers_blue(self) -> None:
        graded = apply_grade(_pixels((100, 100, 100)), ColorGrade(temperature=8000))
        self.assertGreater(graded[0, 0, 0], 100)
        self.assertLess(graded[0, 0, 2], 100)

    def test_positive_tint_lowers_green(self) -> None:
        self.assertLess(apply_grade(_pixels((100, 100, 100)), ColorGrade(tint=100))[0, 0, 1], 100)

    def test_negative_saturation_to_minimum_makes_gray(self) -> None:
        graded = apply_grade(_pixels(WARM_GRAY), ColorGrade(saturation=-100))
        self.assertEqual(len(set(graded[0, 0].tolist())), 1)

    def test_vibrance_lifts_muted_color_more_than_vivid_color(self) -> None:
        muted = apply_grade(_pixels((110, 100, 90)), ColorGrade(vibrance=100))
        vivid = apply_grade(_pixels((250, 40, 40)), ColorGrade(vibrance=100))
        muted_ratio = (int(muted[0, 0, 0]) - int(muted[0, 0, 2])) / 20
        vivid_ratio = (int(vivid[0, 0, 0]) - int(vivid[0, 0, 1])) / 210
        self.assertGreater(muted_ratio, vivid_ratio)

    def test_extreme_values_stay_in_range(self) -> None:
        graded = apply_grade(_pixels((250, 10, 10)), ColorGrade(50000, 150, 100, 100))
        self.assertEqual(graded.dtype, np.uint8)

    def test_gains_are_equal_at_neutral(self) -> None:
        self.assertTrue(np.allclose(channel_gains(5500, 0), 1.0))

    def test_grade_reads_tone_values_and_defaults(self) -> None:
        self.assertTrue(ColorGrade.from_tone({}).is_neutral)
        self.assertEqual(ColorGrade.from_tone({"Temp": 4000, "Tint": 5, "Vibrance": 6, "Saturation": 7}),
                         ColorGrade(4000, 5, 6, 7))


class AutoBalanceTests(unittest.TestCase):
    def test_gray_scene_stays_neutral(self) -> None:
        self.assertEqual(auto_balance((90.0, 90.0, 90.0)), (5500, 0))

    def test_warm_scene_cools_down_and_neutralizes_the_cast(self) -> None:
        temperature, tint = auto_balance(WARM_GRAY)
        self.assertLess(temperature, 5500)
        corrected = apply_grade(_pixels(WARM_GRAY), ColorGrade(temperature, tint))[0, 0]
        self.assertLessEqual(int(corrected.max()) - int(corrected.min()), 3)

    def test_result_stays_inside_slider_ranges(self) -> None:
        temperature, tint = auto_balance((1.0, 255.0, 255.0))
        self.assertTrue(2000 <= temperature <= 50000 and -150 <= tint <= 150)
        temperature, _ = auto_balance((255.0, 255.0, 0.0))
        self.assertGreaterEqual(temperature, 2000)


class WhiteBalanceChoiceTests(unittest.TestCase):
    def test_neutral_values_are_as_shot(self) -> None:
        self.assertEqual(choice_for(5500, 0), AS_SHOT)

    def test_edited_values_are_custom(self) -> None:
        self.assertEqual(choice_for(5600, 0), CUSTOM)
        self.assertEqual(choice_for(5500, 1), CUSTOM)

    def test_choices_start_with_as_shot_and_auto(self) -> None:
        self.assertEqual(CHOICES[:2], (AS_SHOT, AUTO))

    def test_import_settings_hold_neutral_temperature(self) -> None:
        self.assertEqual(import_settings()["Temp"], "5500")


class PreviewGradeTests(unittest.TestCase):
    def test_neutral_grade_returns_the_same_image(self) -> None:
        image = QImage(2, 2, QImage.Format.Format_RGB32)
        self.assertIs(grade_image(image, ColorGrade()), image)

    def test_null_image_is_returned_as_is(self) -> None:
        image = QImage()
        self.assertIs(grade_image(image, ColorGrade(temperature=8000)), image)
        self.assertEqual(average_rgb(image), (1.0, 1.0, 1.0))

    def test_warm_grade_changes_the_pixels(self) -> None:
        image = QImage(3, 2, QImage.Format.Format_RGB32)
        image.fill(QColor(100, 100, 100))
        graded = grade_image(image, ColorGrade(temperature=8000))
        self.assertEqual((graded.width(), graded.height()), (3, 2))
        self.assertGreater(graded.pixelColor(1, 1).red(), 100)
        self.assertLess(graded.pixelColor(1, 1).blue(), 100)

    def test_average_matches_a_solid_color(self) -> None:
        image = QImage(5, 3, QImage.Format.Format_RGB32)
        image.fill(QColor(*WARM_GRAY))
        self.assertEqual(average_rgb(image), tuple(float(value) for value in WARM_GRAY))


class ExportGradeTests(unittest.TestCase):
    def _render(self, settings: dict[str, str]) -> tuple[int, int, int]:
        folder = Path(tempfile.mkdtemp())
        original = folder / "frame.png"
        Image.new("RGB", (8, 8), (100, 100, 100)).save(original)
        return render_photo(original, settings, ExportPreset("a", long_edge=0)).getpixel((2, 2))

    def test_temperature_is_in_the_render(self) -> None:
        warm = self._render(encode_tone({"Temp": 8000}))
        self.assertGreater(warm[0], warm[2])

    def test_saturation_is_in_the_render(self) -> None:
        pixel = self._render(encode_tone({"Saturation": -100, "Temp": 8000}))
        self.assertEqual(len(set(pixel)), 1)

    def test_neutral_settings_keep_the_image(self) -> None:
        image = Image.new("RGB", (4, 4))
        self.assertIs(grade_pil(image, ColorGrade()), image)

    def test_palette_images_are_converted(self) -> None:
        image = Image.new("L", (4, 4), 90)
        self.assertEqual(grade_pil(image, ColorGrade(temperature=8000)).mode, "RGB")


class DevelopPanelBalanceTests(unittest.TestCase):
    def test_choosing_a_preset_sets_temperature_and_tint(self) -> None:
        panel, _ = _panel_with_photo()
        combo = panel._controls.white_balance
        combo.setCurrentText("Tungsten")
        panel._balance._chosen(combo.currentIndex())
        self.assertEqual(_slider(panel, "Temp").value(), 2850)
        self.assertEqual(combo.currentText(), "Tungsten")

    def test_auto_sets_values_from_the_photo_and_stays_editable(self) -> None:
        panel, _ = _panel_with_photo()
        combo = panel._controls.white_balance
        combo.setCurrentText(AUTO)
        panel._balance._chosen(combo.currentIndex())
        self.assertLess(_slider(panel, "Temp").value(), 5500)
        _slider(panel, "Temp").set_value(4321)
        self.assertEqual(combo.currentText(), CUSTOM)
        self.assertEqual(_slider(panel, "Temp").value(), 4321)

    def test_editing_after_as_shot_stores_the_edited_value(self) -> None:
        panel, _ = _panel_with_photo()
        self.assertEqual(panel._controls.white_balance.currentText(), AS_SHOT)
        _slider(panel, "Temp").set_value(6100)
        panel._save_tone()
        from src.develop.tone_store import load_tone
        self.assertEqual(load_tone(panel._catalog, 1)["Temp"], 6100)

    def test_choosing_custom_keeps_the_values(self) -> None:
        panel, _ = _panel_with_photo()
        _slider(panel, "Tint").set_value(30)
        combo = panel._controls.white_balance
        panel._balance._chosen(combo.findText(CUSTOM))
        self.assertEqual(_slider(panel, "Tint").value(), 30)

    def test_returning_to_neutral_by_hand_shows_as_shot(self) -> None:
        panel, _ = _panel_with_photo()
        _slider(panel, "Temp").set_value(7000)
        _slider(panel, "Temp").set_value(5500)
        self.assertEqual(panel._controls.white_balance.currentText(), AS_SHOT)

    def test_reset_restores_neutral_balance_and_label(self) -> None:
        panel, _ = _panel_with_photo()
        _slider(panel, "Temp").set_value(7000)
        panel._reset_controls()
        self.assertEqual(_slider(panel, "Temp").value(), 5500)
        self.assertEqual(panel._controls.white_balance.currentText(), AS_SHOT)

    def test_temperature_changes_the_preview_not_the_original(self) -> None:
        panel, original = _panel_with_photo((100, 100, 100))
        before = original.read_bytes()
        plain = panel._edited_image().pixelColor(2, 2)
        _slider(panel, "Temp").set_value(9000)
        warm = panel._edited_image().pixelColor(2, 2)
        self.assertGreater(warm.red(), plain.red())
        self.assertEqual(original.read_bytes(), before)

    def test_history_step_restores_balance_label(self) -> None:
        panel, _ = _panel_with_photo()
        _slider(panel, "Temp").set_value(7000)
        panel._save_tone()
        panel._on_history_selected(0)
        self.assertEqual(_slider(panel, "Temp").value(), 5500)
        self.assertEqual(panel._controls.white_balance.currentText(), AS_SHOT)


if __name__ == "__main__":
    unittest.main()
