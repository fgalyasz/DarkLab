import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QSplitter

from src.ui.contrast import MINIMUM_BODY_CONTRAST, body_label_contrast
from src.ui.dialogs.import_dialog import ImportDialog
from src.ui.panels.develop_panel import DevelopPanel
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.widgets.collapsible_section import CollapsibleSection, PanelColumn
from src.ui.widgets.filmstrip_widget import FilmstripWidget

APP = QApplication.instance() or QApplication([])
LIBRARY_LEFT = ["Navigator", "Catalog", "Folders", "Collections", "Publish Services"]
LIBRARY_RIGHT = ["Histogram", "Quick Develop", "Keywording", "Keyword List", "Metadata", "Comments"]
DEVELOP_LEFT = ["Navigator", "Presets", "Snapshots", "History", "Collections"]
DEVELOP_RIGHT = [
    "Histogram", "Basic", "Tone Curve", "Color Mixer", "Color Grading", "Detail",
    "Lens Corrections", "Transform", "Effects", "Calibration",
]
TOOL_STRIP_ENTRY_POINTS = ["Crop", "Spot", "Red Eye", "Mask"]
IMPORT_BANDS = ["importSource", "importStage", "importSide"]


def _titles(parent) -> list[str]:
    sections = parent.findChildren(CollapsibleSection)
    return [section.header().findChild(QLabel, "panelTitle").text() for section in sections]


def _section_of(widget) -> CollapsibleSection:
    while not isinstance(widget, CollapsibleSection):
        widget = widget.parentWidget()
    return widget


def _workspace(panel) -> QSplitter:
    return panel.layout().itemAt(0).widget()


def _column(panel, index: int) -> PanelColumn:
    return _workspace(panel).widget(index)


class ClassicLibraryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = LibraryBrowserPanel()

    def tearDown(self) -> None:
        self.panel._cancel_load()
        self.panel.close()

    def test_filmstrip_sits_under_the_main_view(self) -> None:
        layout = self.panel.layout()
        self.assertIsInstance(layout.itemAt(0).widget(), QSplitter)
        self.assertIsInstance(layout.itemAt(1).widget(), FilmstripWidget)

    def test_left_and_right_columns_keep_their_classic_roles(self) -> None:
        self.assertEqual(_workspace(self.panel).count(), 3)
        self.assertEqual(_titles(_column(self.panel, 0)), LIBRARY_LEFT)
        self.assertEqual(_titles(_column(self.panel, 2)), LIBRARY_RIGHT)

    def test_body_labels_meet_the_contrast_floor(self) -> None:
        self.assertGreaterEqual(body_label_contrast(self.panel.styleSheet()), MINIMUM_BODY_CONTRAST)


class ClassicDevelopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.panel = DevelopPanel()

    def tearDown(self) -> None:
        self.panel._cancel_load()
        self.panel.close()

    def test_left_column_hosts_navigator_presets_snapshots_history_collections(self) -> None:
        self.assertEqual(_titles(_workspace(self.panel).widget(0)), DEVELOP_LEFT)

    def test_right_column_panels_follow_the_classic_order(self) -> None:
        shown = [title for title in _titles(_workspace(self.panel).widget(2)) if title != "Crop"]
        self.assertEqual(shown, DEVELOP_RIGHT)

    def test_tool_strip_sits_directly_under_the_histogram(self) -> None:
        histogram = _section_of(self.panel.histogram)
        layout = histogram.parentWidget().layout()
        strip = layout.itemAt(layout.indexOf(histogram) + 1).widget()
        self.assertEqual([button.text() for button in strip.findChildren(QPushButton)], TOOL_STRIP_ENTRY_POINTS)

    def test_body_labels_meet_the_contrast_floor(self) -> None:
        self.assertGreaterEqual(body_label_contrast(self.panel.styleSheet()), MINIMUM_BODY_CONTRAST)


class ClassicImportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dialog = ImportDialog()
        self.dialog.show()

    def tearDown(self) -> None:
        self.dialog.close()

    def test_source_grid_and_options_are_three_distinct_bands(self) -> None:
        splitter = self.dialog.main_splitter
        self.assertEqual([splitter.widget(index).objectName() for index in range(splitter.count())], IMPORT_BANDS)

    def test_copy_move_add_share_one_choice_row(self) -> None:
        parents = {self.dialog._mode_buttons[mode].parentWidget() for mode in ("import", "move", "add")}
        self.assertEqual(len(parents), 1)
        self.assertNotIn(self.dialog._mode_buttons["culling"].parentWidget(), parents)

    def test_side_panel_has_no_horizontal_scrollbar_at_the_default_width(self) -> None:
        side = self.dialog.main_splitter.widget(2)
        scroll = side.layout().itemAt(0).widget()
        self.assertEqual(scroll.horizontalScrollBar().maximum(), 0)
        self.assertLessEqual(scroll.widget().minimumSizeHint().width(), side.width())


if __name__ == "__main__":
    unittest.main()
