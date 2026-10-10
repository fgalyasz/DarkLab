import os
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.imaging.preview_tone import tone_channel
from src.ui.import_summary import format_byte_count, import_status_text
from src.ui.library_catalog import (
    existing_paths, filter_paths, keyword_tokens, matches_rating,
    merge_catalog_paths, previous_import_directory, sort_paths,
)
from src.ui.widgets.histogram_widget import add_rgb_sample, bin_index, empty_channel


class PreviewToneTests(unittest.TestCase):
    def test_exposure_brightens_midtone(self) -> None:
        self.assertGreater(tone_channel(128, 50, 0), 128)

    def test_negative_exposure_darkens_midtone(self) -> None:
        self.assertLess(tone_channel(128, -50, 0), 128)

    def test_channel_stays_in_range(self) -> None:
        self.assertEqual(tone_channel(255, 100, 0), 255)
        self.assertEqual(tone_channel(0, -100, 0), 0)


class ImportSummaryTests(unittest.TestCase):
    def test_byte_units(self) -> None:
        self.assertEqual(format_byte_count(512), "512 bytes")
        self.assertEqual(format_byte_count(2048), "2.0 KB")

    def test_status_without_selection(self) -> None:
        self.assertEqual(import_status_text(0, 0, 0), "0 photos / 0 bytes")

    def test_status_with_selection(self) -> None:
        text = import_status_text(10, 2, 2048)
        self.assertEqual(text, "2 of 10 photos / 2.0 KB")


class CatalogTests(unittest.TestCase):
    def test_merge_keeps_order_and_drops_duplicates(self) -> None:
        merged = merge_catalog_paths(["a.jpg"], [Path("b.jpg"), Path("a.jpg")])
        self.assertEqual(merged, ["a.jpg", "b.jpg"])

    def test_existing_paths_skip_missing_files(self) -> None:
        self.assertEqual(existing_paths(["/missing/photo.jpg", 12]), [])

    def test_filter_and_sort_names(self) -> None:
        folder = Path(tempfile.mkdtemp())
        first = folder / "b.jpg"
        second = folder / "a.jpg"
        first.write_bytes(b"x")
        second.write_bytes(b"x")
        named = filter_paths([first, second], "a")
        self.assertEqual(named, [second])
        self.assertEqual(sort_paths([first, second], "name"), [second, first])

    def test_keywords_and_rating(self) -> None:
        self.assertEqual(keyword_tokens("cat, dog\nbird"), ["cat", "dog", "bird"])
        self.assertTrue(matches_rating("4", "3"))
        self.assertFalse(matches_rating("2", "3"))
        self.assertTrue(matches_rating("0", "any"))

    def test_previous_import_directory(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            settings = {
                "active_destination_preset": "Default",
                "destination_presets": {"Default": {"target_root": folder}},
            }
            self.assertEqual(previous_import_directory(settings), Path(folder))
        self.assertIsNone(previous_import_directory({}))


class HistogramTests(unittest.TestCase):
    def test_sample_lands_in_upper_bin(self) -> None:
        bins = (empty_channel(), empty_channel(), empty_channel())
        add_rgb_sample(bins, 255, 0, 128)
        self.assertEqual(bins[0][bin_index(255)], 1)
        self.assertEqual(bins[1][bin_index(0)], 1)
        self.assertEqual(sum(bins[2]), 1)


class LightroomShellTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from PyQt6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def test_develop_panel_matches_lightroom_sections(self) -> None:
        from src.ui.panels.develop_panel import DevelopPanel
        from src.ui.widgets.collapsible_section import CollapsibleSection
        panel = DevelopPanel()
        panel.show()
        titles = [section.header().findChild(type(panel.filename_label)).text() for section in panel.findChildren(CollapsibleSection)]
        self.assertIn("Basic", titles)
        self.assertIn("Tone Curve", titles)
        self.assertIn("Color Grading", titles)
        self.assertIn("Calibration", titles)
        self.assertIn("Navigator", titles)
        panel._reset_controls()
        panel._cancel_load()
        panel.close()

    def test_main_window_modules(self) -> None:
        from src.ui.main_window import MainWindow
        with isolated_config():
            window = MainWindow()
            self.assertEqual(set(window.panels), {"library", "develop", "map", "book", "slideshow", "print", "website"})
            self.assertEqual(window.panel_container.currentWidget(), window.panels["library"])
            library = window.panels["library"]
            self.assertTrue(hasattr(library, "navigator"))
            self.assertTrue(hasattr(library, "filmstrip"))
            library._cancel_load()
            window.close()

    def test_panel_header_collapses_and_expands(self) -> None:
        from PyQt6.QtCore import Qt
        from PyQt6.QtTest import QTest
        from PyQt6.QtWidgets import QLabel
        from src.ui.widgets.collapsible_section import HEADER_HEIGHT, CollapsibleSection
        content = QLabel("Navigator body")
        section = CollapsibleSection("Navigator", content)
        section.show()
        self.assertTrue(content.isVisible())
        QTest.mouseClick(section.header(), Qt.MouseButton.LeftButton)
        self.assertFalse(content.isVisible())
        self.assertEqual(section.maximumHeight(), HEADER_HEIGHT)
        section.toggle()
        self.assertTrue(content.isVisible())
        section.close()

    def test_import_dialog_layout(self) -> None:
        from src.ui.dialogs.import_dialog import ImportDialog
        dialog = ImportDialog()
        dialog.show()
        self.assertEqual(dialog.source_prompt.text(), "Please select a source.")
        self.assertEqual(dialog.center_stack.currentIndex(), 0)
        self.assertIn("photos", dialog.import_status_label.text())
        self.assertTrue(dialog.culling_bar.isHidden())
        dialog._set_import_mode("culling")
        self.assertTrue(dialog.culling_bar.isVisible())
        dialog._set_import_mode("add")
        self.assertEqual(dialog.import_button.text(), "Add")
        dialog.close()


def isolated_config() -> ExitStack:
    stack = ExitStack()
    stack.enter_context(patch("src.ui.main_window.ConfigManager.get_current_panel", return_value="library"))
    stack.enter_context(patch("src.ui.main_window.ConfigManager.set_current_panel"))
    stack.enter_context(patch("src.ui.main_window.ConfigManager.set_window_geometry"))
    stack.enter_context(patch("src.ui.main_window.ConfigManager.set"))
    stack.enter_context(patch("src.ui.main_window.ConfigManager.get_window_geometry", return_value=None))
    return stack


if __name__ == "__main__":
    unittest.main()
