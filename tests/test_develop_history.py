import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PIL import Image
from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.file_hash import content_hash
from src.catalog.index_images import list_index_images
from src.develop.crop_settings import CropSettings
from src.develop.crop_store import load_crop, save_crop
from src.develop.history import (
    IMPORT_LABEL, SAVED_LABEL, DevelopHistory, develop_settings, import_settings, step_label,
)
from src.develop.tone_store import load_tone, save_tone
from src.importing.originals import import_originals

APP = QApplication.instance() or QApplication([])
BASE = import_settings()


def _changed(**values: str) -> dict[str, str]:
    return {**BASE, **values}


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
    panel._show_photo(list_index_images(catalog)[0])
    return panel


def _slider(panel, title: str):
    return next(row for row in panel._controls.sliders if row.title == title)


def _edit(panel, title: str, value: int) -> None:
    _slider(panel, title).set_value(value)
    panel._save_tone()


class StepLabelTests(unittest.TestCase):
    def test_single_tone_change_names_the_slider_and_value(self) -> None:
        self.assertEqual(step_label(BASE, _changed(Exposure="12")), "Exposure 12")

    def test_single_crop_change_is_spaced(self) -> None:
        self.assertEqual(step_label(BASE, _changed(CropLeft="5")), "Crop Left 5")

    def test_lock_change_reads_on_and_off(self) -> None:
        self.assertEqual(step_label(BASE, _changed(CropAspectLock="1")), "Crop Aspect Lock on")
        self.assertEqual(step_label(_changed(CropAspectLock="1"), BASE), "Crop Aspect Lock off")

    def test_several_crop_changes_are_one_crop_step(self) -> None:
        self.assertEqual(step_label(BASE, _changed(CropLeft="5", CropTop="5")), "Crop")

    def test_mixed_changes_are_counted(self) -> None:
        self.assertEqual(step_label(BASE, _changed(Exposure="5", CropTop="5")), "2 settings")


class DevelopHistoryTests(unittest.TestCase):
    def test_history_starts_at_import(self) -> None:
        history = DevelopHistory(BASE)
        self.assertEqual([step.label for step in history.steps], [IMPORT_LABEL])
        self.assertEqual(history.import_step.settings, BASE)

    def test_import_settings_are_the_defaults(self) -> None:
        self.assertEqual(import_settings(), develop_settings({}, CropSettings()) | import_settings())
        self.assertEqual(BASE["Exposure"], "0")
        self.assertEqual(BASE["CropLeft"], "0")

    def test_record_adds_a_step(self) -> None:
        history = DevelopHistory(BASE)
        self.assertTrue(history.record(_changed(Exposure="5")))
        self.assertEqual(history.current_index, 1)

    def test_record_of_the_same_settings_adds_nothing(self) -> None:
        history = DevelopHistory(BASE)
        self.assertFalse(history.record(dict(BASE)))
        self.assertEqual(len(history.steps), 1)

    def test_select_returns_that_steps_settings(self) -> None:
        history = DevelopHistory(BASE)
        history.record(_changed(Exposure="5"))
        history.record(_changed(Exposure="5", Contrast="9"))
        self.assertEqual(history.select(1), _changed(Exposure="5"))
        self.assertEqual(history.current_settings(), _changed(Exposure="5"))

    def test_change_after_selecting_an_older_step_drops_later_steps(self) -> None:
        history = DevelopHistory(BASE)
        history.record(_changed(Exposure="5"))
        history.record(_changed(Exposure="9"))
        history.select(1)
        history.record(_changed(Exposure="7"))
        self.assertEqual([step.label for step in history.steps], [IMPORT_LABEL, "Exposure 5", "Exposure 7"])

    def test_select_out_of_range_is_refused(self) -> None:
        history = DevelopHistory(BASE)
        for index in (-1, 1):
            with self.assertRaises(IndexError):
                history.select(index)

    def test_record_accepts_a_label(self) -> None:
        history = DevelopHistory(BASE)
        history.record(_changed(Exposure="5"), SAVED_LABEL)
        self.assertEqual(history.steps[1].label, SAVED_LABEL)


class DevelopHistoryPanelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()
        self.panel = _panel(self.catalog)

    def _labels(self) -> list[str]:
        widget = self.panel.history_widget
        return [widget.item(row).text() for row in range(widget.count())]

    def test_new_photo_shows_only_the_import_step(self) -> None:
        self.assertEqual(self._labels(), [IMPORT_LABEL])

    def test_each_settled_change_is_a_step(self) -> None:
        _edit(self.panel, "Exposure", 10)
        _edit(self.panel, "Contrast", -5)
        self.assertEqual(self._labels(), [IMPORT_LABEL, "Exposure 10", "Contrast -5"])
        self.assertEqual(self.panel.history_widget.currentRow(), 2)

    def test_selecting_the_older_step_restores_those_settings(self) -> None:
        _edit(self.panel, "Exposure", 10)
        _edit(self.panel, "Contrast", -5)
        self.panel.history_widget.setCurrentRow(1)
        self.assertEqual((_slider(self.panel, "Exposure").value(), _slider(self.panel, "Contrast").value()), (10, 0))
        self.assertEqual(load_tone(self.catalog, 1)["Contrast"], 0)

    def test_selecting_a_step_does_not_add_a_step(self) -> None:
        _edit(self.panel, "Exposure", 10)
        self.panel.history_widget.setCurrentRow(0)
        self.assertEqual(len(self._labels()), 2)
        self.assertEqual(_slider(self.panel, "Exposure").value(), 0)

    def test_crop_steps_restore_crop(self) -> None:
        _edit(self.panel, "Left", 20)
        self.panel.history_widget.setCurrentRow(0)
        self.assertEqual(load_crop(self.catalog, 1), CropSettings())

    def test_pending_edit_is_kept_before_stepping_back(self) -> None:
        _edit(self.panel, "Exposure", 10)
        _slider(self.panel, "Contrast").set_value(30)
        self.panel.history_widget.setCurrentRow(0)
        self.assertEqual(_slider(self.panel, "Contrast").value(), 0)
        self.assertEqual(self._labels(), [IMPORT_LABEL, "Exposure 10", "Contrast 30"])

    def test_stored_settings_start_as_a_saved_settings_step(self) -> None:
        save_tone(self.catalog, 1, {"Exposure": 40})
        save_crop(self.catalog, 1, CropSettings(left=5))
        panel = _panel(self.catalog)
        self.assertEqual(self._labels_of(panel), [IMPORT_LABEL, SAVED_LABEL])

    def _labels_of(self, panel) -> list[str]:
        widget = panel.history_widget
        return [widget.item(row).text() for row in range(widget.count())]

    def test_history_is_kept_per_photo_while_the_panel_lives(self) -> None:
        _edit(self.panel, "Exposure", 10)
        self.panel._show_photo(list_index_images(self.catalog)[0])
        self.assertEqual(self._labels(), [IMPORT_LABEL, "Exposure 10"])

    def test_same_titled_sliders_elsewhere_do_not_change_stored_tone(self) -> None:
        sliders = [row for row in self.panel._controls.sliders if row.title == "Highlights"]
        sliders[-1].set_value(60)
        self.panel._save_tone()
        self.assertEqual(load_tone(self.catalog, 1)["Highlights"], 0)
        self.assertEqual(self._labels(), [IMPORT_LABEL])

    def test_no_selection_row_is_ignored(self) -> None:
        self.panel._on_history_selected(-1)
        self.assertEqual(self._labels(), [IMPORT_LABEL])

    def test_history_with_no_current_photo_is_ignored(self) -> None:
        self.panel._current = None
        self.panel._on_history_selected(0)
        self.panel._show_current_history()
        self.assertEqual(self._labels(), [IMPORT_LABEL])

    def test_failed_save_logs_and_adds_no_step(self) -> None:
        with patch("src.ui.panels.develop_panel.save_tone", side_effect=__import__("sqlite3").Error("locked")):
            _edit(self.panel, "Exposure", 10)
        self.assertEqual(self._labels(), [IMPORT_LABEL])


class BeforeAfterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog, self.original = _catalog_with_photo()
        self.panel = _panel(self.catalog)

    def _preview_width(self) -> int:
        return self.panel.preview.pixmap().width()

    def test_toggle_shows_the_import_view_and_back(self) -> None:
        _edit(self.panel, "Left", 50)
        cropped = self._preview_width()
        self.panel.compare_button.setChecked(True)
        self.assertGreater(self._preview_width(), cropped)
        self.panel.compare_button.setChecked(False)
        self.assertEqual(self._preview_width(), cropped)

    def test_toggle_writes_no_step_and_no_settings(self) -> None:
        _edit(self.panel, "Exposure", 10)
        steps = self.panel.history_widget.count()
        self.panel.compare_button.setChecked(True)
        self.assertEqual(self.panel.history_widget.count(), steps)
        self.assertEqual(load_tone(self.catalog, 1)["Exposure"], 10)
        self.assertEqual(_slider(self.panel, "Exposure").value(), 10)

    def test_editing_while_comparing_returns_to_the_current_settings(self) -> None:
        self.panel.compare_button.setChecked(True)
        _slider(self.panel, "Exposure").set_value(5)
        self.assertFalse(self.panel.compare_button.isChecked())

    def test_compare_never_touches_the_original(self) -> None:
        before = content_hash(self.original)
        _edit(self.panel, "Exposure", 10)
        self.panel.compare_button.setChecked(True)
        self.panel.history_widget.setCurrentRow(0)
        self.assertEqual(content_hash(self.original), before)


if __name__ == "__main__":
    unittest.main()
