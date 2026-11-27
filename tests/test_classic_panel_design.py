import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QWidget

from src.ui.contrast import MINIMUM_BODY_CONTRAST, contrast_ratio
from src.ui.density import Density
from src.ui.develop_sections import DevelopControls, basic_panel
from src.ui.panels.develop_panel import DevelopPanel
from src.ui.panels.library_browser_panel import LibraryBrowserPanel
from src.ui.themes import StyleSheet
from src.ui.widgets.collapsible_section import CollapsibleSection
from src.ui.widgets.develop_group import DevelopGroup
from src.ui.widgets.etched_divider import MAJOR_HEIGHT, SOFT_HEIGHT, EtchedDivider
from src.ui.widgets.slider_geometry import (
    format_slider_value, handle_center_x, pointer_polygon, tick_positions, value_ratio,
)
from src.ui.widgets.slider_row import SLIDER_ROW_HEIGHT, DevelopSlider, SliderRow

APP = QApplication.instance() or QApplication([])


class SliderGeometryTests(unittest.TestCase):
    def test_value_ratio_normalizes_and_clamps(self) -> None:
        self.assertEqual(value_ratio(0, -100, 100), 0.5)
        self.assertEqual(value_ratio(-200, -100, 100), 0.0)
        self.assertEqual(value_ratio(200, -100, 100), 1.0)
        self.assertEqual(value_ratio(10, 10, 10), 0.0)

    def test_handle_center_x_maps_and_handles_degenerate_span(self) -> None:
        self.assertEqual(handle_center_x(0.0, 10, 110), 10)
        self.assertEqual(handle_center_x(0.5, 10, 110), 60)
        self.assertEqual(handle_center_x(1.0, 10, 110), 110)
        self.assertEqual(handle_center_x(2.0, 10, 110), 110)
        self.assertEqual(handle_center_x(0.5, 20, 10), 20)

    def test_tick_positions_mark_ends_and_center_as_major(self) -> None:
        ticks = tick_positions(0, 80, 9)
        self.assertEqual(len(ticks), 9)
        self.assertEqual([index for index, (_, major) in enumerate(ticks) if major], [0, 4, 8])
        self.assertEqual(ticks[0][0], 0)
        self.assertEqual(ticks[4][0], 40)
        self.assertEqual(ticks[8][0], 80)

    def test_tick_positions_return_empty_on_invalid_inputs(self) -> None:
        self.assertEqual(tick_positions(10, 10, 9), ())
        self.assertEqual(tick_positions(0, 80, 1), ())

    def test_pointer_polygon_points_upward_at_center(self) -> None:
        points = pointer_polygon(50, 5)
        self.assertEqual(len(points), 5)
        self.assertEqual(points[0], (50, 5))
        self.assertLess(points[0][1], points[1][1])
        self.assertEqual(points[1][1], points[4][1])
        self.assertEqual(points[2][1], points[3][1])

    def test_format_slider_value_covers_exposure_temp_and_signed(self) -> None:
        self.assertEqual(format_slider_value("Exposure", 0, -500), "0.00")
        self.assertEqual(format_slider_value("Exposure", 125, -500), "+1.25")
        self.assertEqual(format_slider_value("Exposure", -50, -500), "-0.50")
        self.assertEqual(format_slider_value("Temp", 5500, 2000), "5 500")
        self.assertEqual(format_slider_value("Contrast", 15, -100), "+15")
        self.assertEqual(format_slider_value("Contrast", -30, -100), "-30")
        self.assertEqual(format_slider_value("Contrast", 0, -100), "0")
        self.assertEqual(format_slider_value("Amount", 40, 0), "40")


class ClassicPanelDesignTests(unittest.TestCase):
    def test_etched_dividers_have_expected_heights_and_paint(self) -> None:
        major = EtchedDivider("major")
        soft = EtchedDivider("soft")
        self.assertEqual(major.height(), MAJOR_HEIGHT)
        self.assertEqual(soft.height(), SOFT_HEIGHT)
        self.assertEqual(major.kind, "major")
        self.assertEqual(soft.kind, "soft")
        major.resize(200, MAJOR_HEIGHT)
        soft.resize(200, SOFT_HEIGHT)
        major.grab()
        soft.grab()
        major.close()
        soft.close()

    def test_basic_panel_has_major_and_soft_dividers(self) -> None:
        panel = basic_panel(DevelopControls())
        dividers = panel.findChildren(EtchedDivider)
        major = [item for item in dividers if item.kind == "major"]
        soft = [item for item in dividers if item.kind == "soft"]
        self.assertEqual(len(major), 3)
        self.assertEqual(len(soft), 2)
        panel.close()

    def test_slider_row_right_aligns_caption_and_value(self) -> None:
        row = SliderRow("Highlights", -100, 100, 25)
        caption = row.findChild(QLabel, "sliderCaption")
        value = row.findChild(QLabel, "sliderValue")
        self.assertEqual(row.height(), SLIDER_ROW_HEIGHT)
        self.assertTrue(bool(caption.alignment() & Qt.AlignmentFlag.AlignRight))
        self.assertTrue(bool(value.alignment() & Qt.AlignmentFlag.AlignRight))
        self.assertEqual(value.text(), "+25")
        row.set_compact_caption(46)
        self.assertEqual(caption.width(), 46)
        self.assertTrue(bool(caption.alignment() & Qt.AlignmentFlag.AlignLeft))
        row.close()

    def test_develop_slider_paints_and_handles_pointer_drag(self) -> None:
        slider = DevelopSlider()
        slider.setRange(-100, 100)
        slider.setValue(0)
        slider.resize(160, 18)
        slider.show()
        APP.processEvents()
        slider.grab()
        press = QMouseEvent(
            QMouseEvent.Type.MouseButtonPress,
            QPointF(150.0, 9.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
        )
        slider.mousePressEvent(press)
        self.assertGreater(slider.value(), 50)
        release = QMouseEvent(
            QMouseEvent.Type.MouseButtonRelease,
            QPointF(150.0, 9.0),
            Qt.MouseButton.LeftButton,
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
        )
        slider.mouseReleaseEvent(release)
        slider.close()

    def test_column_headers_align_left_and_right_like_classic(self) -> None:
        panel = DevelopPanel()
        splitter = panel.layout().itemAt(0).widget()
        left_sections = splitter.widget(0).findChildren(CollapsibleSection)
        right_sections = splitter.widget(2).findChildren(CollapsibleSection)
        self.assertTrue(all(section.header().arrow_on_left for section in left_sections))
        self.assertTrue(all(not section.header().arrow_on_left for section in right_sections))
        panel._cancel_load()
        panel.close()

    def test_library_columns_and_quick_develop_use_classic_chrome(self) -> None:
        panel = LibraryBrowserPanel()
        splitter = panel.layout().itemAt(0).widget()
        left_sections = splitter.widget(0).findChildren(CollapsibleSection)
        right_sections = splitter.widget(2).findChildren(CollapsibleSection)
        self.assertTrue(all(section.header().arrow_on_left for section in left_sections))
        self.assertTrue(all(not section.header().arrow_on_left for section in right_sections))
        self.assertIsInstance(panel.exposure_slider, DevelopSlider)
        self.assertIsInstance(panel.contrast_slider, DevelopSlider)
        panel._cancel_load()
        panel.close()

    def test_panel_surface_text_meets_contrast_floor(self) -> None:
        self.assertGreaterEqual(contrast_ratio((224, 224, 224), (80, 80, 80)), MINIMUM_BODY_CONTRAST)
        self.assertGreaterEqual(contrast_ratio((222, 222, 222), (80, 80, 80)), MINIMUM_BODY_CONTRAST)
        self.assertIn("QScrollBar:vertical", StyleSheet.LIGHTROOM)
        self.assertEqual(Density.PANEL_CORNER_RADIUS_PX, 0)

    def test_develop_group_without_divider_collapses_to_header_height(self) -> None:
        group = DevelopGroup("Treatment", show_divider=False)
        group.toggle()
        self.assertEqual(group.maximumHeight(), Density.GROUP_HEADER_HEIGHT)
        group.close()

    def test_treatment_buttons_display_bw_with_escaped_ampersand(self) -> None:
        panel = basic_panel(DevelopControls())
        texts = [button.text() for button in panel.findChildren(QPushButton)]
        self.assertIn("Color", texts)
        self.assertIn("B&&W", texts)
        panel.close()


if __name__ == "__main__":
    unittest.main()
