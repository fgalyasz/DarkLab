import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget

from src.ui.density import Density
from src.ui.panels.base_panel import BasePanel
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.themes import StyleSheet
from src.ui.widgets.color_wheel import ColorWheel
from src.ui.widgets.module_bar import ModuleBar
from src.ui.widgets.slider_row import SLIDER_ROW_HEIGHT, SliderRow
from src.ui.develop_sections import DevelopControls, basic_panel
from src.ui.widgets.collapsible_section import HEADER_HEIGHT, CollapsibleSection
from src.ui.widgets.develop_group import DevelopGroup

APP = QApplication.instance() or QApplication([])


class DensityCapsTests(unittest.TestCase):
    def test_typography_caps_stay_classic(self) -> None:
        self.assertLessEqual(Density.BODY_PX, 11)
        self.assertLessEqual(Density.HEADER_PX, 11)
        self.assertLessEqual(Density.HINT_PX, 10)
        self.assertLessEqual(Density.TITLE_PX, 13)

    def test_chrome_heights_stay_compact(self) -> None:
        self.assertLessEqual(Density.MODULE_BAR_HEIGHT, 30)
        self.assertLessEqual(Density.PANEL_HEADER_HEIGHT, 22)
        self.assertLessEqual(Density.FILTER_BAR_HEIGHT, 28)
        self.assertLessEqual(Density.TOOL_BAR_HEIGHT, 32)
        self.assertEqual(HEADER_HEIGHT, Density.PANEL_HEADER_HEIGHT)

    def test_stylesheet_uses_body_font(self) -> None:
        self.assertIn(f"font-size: {Density.BODY_PX}px", StyleSheet.LIGHTROOM)
        self.assertIn(f"font-size: {Density.HEADER_PX}px", StyleSheet.LIGHTROOM)


class DensityWidgetTests(unittest.TestCase):
    def test_module_bar_uses_compact_height(self) -> None:
        bar = ModuleBar((("library", "Library"), ("develop", "Develop")), "Catalog")
        self.assertEqual(bar.height(), Density.MODULE_BAR_HEIGHT)
        bar.close()

    def test_placeholder_title_uses_title_cap(self) -> None:
        panel = BasePanel("map")
        self.assertIn(f"font-size: {Density.TITLE_PX}px", panel.title_label.styleSheet())
        panel.close()

    def test_slider_row_stays_single_line_in_narrow_panel(self) -> None:
        host = QWidget()
        host.setFixedWidth(280)
        row = SliderRow("Highlights", -100, 100, 0)
        row.setParent(host)
        host.show()
        APP.processEvents()
        self.assertEqual(row.height(), SLIDER_ROW_HEIGHT)
        caption = row.layout().itemAt(0).widget()
        self.assertFalse(caption.wordWrap())
        self.assertEqual(caption.width(), Density.SLIDER_CAPTION_WIDTH)
        host.close()

    def test_tone_sliders_stay_dense_inside_a_tall_group(self) -> None:
        group = DevelopGroup("Tone")
        for index in range(6):
            group.body_layout().addWidget(SliderRow(f"S{index}", -100, 100, 0))
        host = QWidget()
        host.setFixedSize(280, 600)
        wrap = QVBoxLayout(host)
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.addWidget(group)
        wrap.addStretch(1)
        host.show()
        APP.processEvents()
        rows = group.findChildren(SliderRow)
        self.assertEqual(len(rows), 6)
        self.assertTrue(all(row.height() == SLIDER_ROW_HEIGHT for row in rows))
        top = rows[0].mapTo(group, rows[0].rect().topLeft()).y()
        bottom = rows[-1].mapTo(group, rows[-1].rect().bottomLeft()).y()
        self.assertLessEqual(bottom - top + 1, 6 * SLIDER_ROW_HEIGHT + 4)
        host.close()

    def test_collapsed_groups_keep_tight_gaps(self) -> None:
        panel = basic_panel(DevelopControls())
        host = QWidget()
        host.setFixedSize(300, 700)
        wrap = QVBoxLayout(host)
        wrap.setContentsMargins(0, 0, 0, 0)
        wrap.addWidget(panel)
        wrap.addStretch(1)
        host.show()
        APP.processEvents()
        groups = {group.title(): group for group in panel.findChildren(DevelopGroup)}
        groups["Tone"].toggle()
        groups["Presence"].toggle()
        APP.processEvents()
        ordered = [groups[name] for name in ("Treatment", "WB", "Tone", "Presence")]
        gaps = [ordered[i + 1].y() - (ordered[i].y() + ordered[i].height()) for i in range(3)]
        self.assertTrue(all(gap <= 2 for gap in gaps), gaps)
        host.close()

    def test_three_color_wheels_fit_grading_column(self) -> None:
        row = QWidget()
        total = 0
        for title in ("Shadows", "Midtones", "Highlights"):
            wheel = ColorWheel(title)
            self.assertLessEqual(wheel.width(), Density.COLOR_WHEEL_WIDTH)
            total += wheel.width()
        self.assertLessEqual(total + 8, Density.GRADING_COLUMN_MIN)
        row.close()

    def test_library_filter_and_toolbar_heights(self) -> None:
        panel = LibraryBrowserPanel()
        filter_bar = panel.layout().itemAt(0).widget().widget(1).layout().itemAt(0).widget()
        tool_bar = panel.layout().itemAt(2).widget()
        self.assertEqual(filter_bar.height(), Density.FILTER_BAR_HEIGHT)
        self.assertEqual(tool_bar.height(), Density.TOOL_BAR_HEIGHT)
        panel._cancel_load()
        panel.close()

    def test_panel_header_height_matches_density(self) -> None:
        section = CollapsibleSection("Navigator", QWidget())
        self.assertEqual(section.header().height(), Density.PANEL_HEADER_HEIGHT)
        section.close()

    def test_stylesheet_uses_panel_corner_radius(self) -> None:
        self.assertIn(f"border-radius: {Density.PANEL_CORNER_RADIUS_PX}px", StyleSheet.LIGHTROOM)
        self.assertGreaterEqual(Density.PANEL_CORNER_RADIUS_PX, 8)

    def test_develop_groups_collapse_like_classic(self) -> None:
        group = DevelopGroup("Tone")
        body = group.body_layout().parentWidget()
        group.show()
        APP.processEvents()
        self.assertTrue(group.is_expanded())
        self.assertTrue(body.isVisible())
        group.toggle()
        APP.processEvents()
        self.assertFalse(group.is_expanded())
        self.assertFalse(body.isVisible())
        group.close()

    def test_basic_panel_hosts_collapsible_groups(self) -> None:
        panel = basic_panel(DevelopControls())
        groups = panel.findChildren(DevelopGroup)
        self.assertEqual([group.title() for group in groups], ["Treatment", "WB", "Tone", "Presence"])
        self.assertTrue(all(group.is_expanded() for group in groups))
        panel.close()


if __name__ == "__main__":
    unittest.main()
