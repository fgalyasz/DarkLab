import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.develop_settings import merge_develop_settings, read_develop_settings, write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.index_images import list_index_images
from src.develop.tone_settings import TONE_KEYS, decode_tone, encode_tone
from src.develop.tone_store import load_tone, save_tone
from src.importing.originals import import_originals

APP = QApplication.instance() or QApplication([])
TONE = {"Exposure": 120, "Contrast": -15, "Highlights": 5, "Shadows": 40, "Whites": -3, "Blacks": 9}
SAVE_ERROR = "src.ui.panels.develop_panel.save_tone"


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


def _slider(panel, title: str):
    return next(row for row in panel._controls.sliders if row.title == title)


class ToneSettingsTests(unittest.TestCase):
    def test_encode_keeps_only_tone_keys(self) -> None:
        encoded = encode_tone({"Exposure": 5, "Texture": 7})
        self.assertEqual(encoded, {"Exposure": "5"})

    def test_decode_round_trips_every_tone_key(self) -> None:
        self.assertEqual(decode_tone(encode_tone(TONE)), TONE)

    def test_decode_ignores_missing_and_invalid_values(self) -> None:
        self.assertEqual(decode_tone({"Exposure": "0.5", "Contrast": "x", "Shadows": "-4"}), {"Shadows": -4})

    def test_tone_keys_are_the_six_tone_sliders(self) -> None:
        self.assertEqual(len(TONE_KEYS), 6)


class ToneStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()

    def test_saved_tone_loads_again(self) -> None:
        save_tone(self.catalog, 1, TONE)
        self.assertEqual(load_tone(self.catalog, 1), TONE)

    def test_photo_without_tone_loads_empty(self) -> None:
        self.assertEqual(load_tone(self.catalog, 1), {})

    def test_save_keeps_settings_that_develop_does_not_edit(self) -> None:
        write_develop_settings(self.catalog, 1, {"Rating": "3", "Exposure": "1"})
        save_tone(self.catalog, 1, {"Exposure": 9})
        self.assertEqual(read_develop_settings(self.catalog, 1), {"Rating": "3", "Exposure": "9"})

    def test_merge_leaves_the_original_unchanged(self) -> None:
        before = content_hash(self.original)
        merge_develop_settings(self.catalog, 1, {"Exposure": "2"})
        self.assertEqual(content_hash(self.original), before)


class DevelopPanelToneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()
        self.index = list_index_images(self.catalog)[0]

    def test_tone_survives_reopening_the_catalog(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        _slider(panel, "Exposure").set_value(150)
        _slider(panel, "Blacks").set_value(-20)
        panel._save_tone()
        reopened = _panel(self.catalog)
        reopened._show_photo(self.index)
        self.assertEqual(_slider(reopened, "Exposure").value(), 150)
        self.assertEqual(_slider(reopened, "Blacks").value(), -20)

    def test_original_hash_is_unchanged_by_saving(self) -> None:
        before = content_hash(self.original)
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        _slider(panel, "Contrast").set_value(30)
        panel._save_tone()
        self.assertEqual(content_hash(self.original), before)

    def test_photo_without_settings_shows_defaults(self) -> None:
        panel = _panel(self.catalog)
        _slider(panel, "Exposure").set_value(80)
        panel._save_timer.stop()
        panel._show_photo(self.index)
        self.assertEqual(_slider(panel, "Exposure").value(), 0)

    def test_loading_does_not_schedule_a_save(self) -> None:
        save_tone(self.catalog, 1, TONE)
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        self.assertFalse(panel._save_timer.isActive())
        self.assertEqual(_slider(panel, "Shadows").value(), 40)

    def test_moving_a_tone_slider_schedules_a_save(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        _slider(panel, "Whites").set_value(10)
        self.assertTrue(panel._save_timer.isActive())

    def test_other_sliders_do_not_schedule_a_save(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        _slider(panel, "Texture").set_value(10)
        self.assertFalse(panel._save_timer.isActive())

    def test_pending_save_flushes_before_the_next_photo(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        _slider(panel, "Exposure").set_value(60)
        panel._show_photo(self.index)
        self.assertEqual(load_tone(self.catalog, 1)["Exposure"], 60)

    def test_hiding_the_panel_flushes_a_pending_save(self) -> None:
        panel = _panel(self.catalog)
        panel.show()
        panel._show_photo(self.index)
        _slider(panel, "Exposure").set_value(70)
        panel.hide()
        self.assertEqual(load_tone(self.catalog, 1)["Exposure"], 70)

    def test_folder_photo_without_index_id_is_not_saved(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.original)
        _slider(panel, "Exposure").set_value(10)
        panel._save_tone()
        self.assertEqual(load_tone(self.catalog, 1), {})

    def test_save_without_a_catalog_does_nothing(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        panel.show_catalog(None)
        panel._current = self.index
        panel._save_tone()
        self.assertEqual(load_tone(self.catalog, 1), {})

    def test_database_failure_is_logged_and_not_raised(self) -> None:
        panel = _panel(self.catalog)
        panel._show_photo(self.index)
        with patch(SAVE_ERROR, side_effect=sqlite3.OperationalError("locked")):
            with self.assertLogs("src.ui.panels.develop_panel", level="ERROR") as logged:
                panel._save_tone()
        self.assertIn("locked", logged.output[0])


if __name__ == "__main__":
    unittest.main()
