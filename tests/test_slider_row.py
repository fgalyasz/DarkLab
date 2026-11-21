import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QApplication

from src.ui.widgets.slider_row import COARSE_STEP, FINE_STEP, SliderRow

APP = QApplication.instance() or QApplication([])


class SliderRowTests(unittest.TestCase):
    def test_double_click_restores_default(self) -> None:
        row = SliderRow("Contrast", -100, 100, 0)
        row.set_value(40)
        row._slider.reset_requested.emit()
        self.assertEqual(row.value(), 0)

    def test_arrow_key_nudges_by_fine_step(self) -> None:
        row = SliderRow("Contrast", -100, 100, 0)
        _press(row, Qt.Key.Key_Right)
        self.assertEqual(row.value(), FINE_STEP)
        _press(row, Qt.Key.Key_Left)
        self.assertEqual(row.value(), 0)

    def test_shift_arrow_nudges_by_coarse_step(self) -> None:
        row = SliderRow("Contrast", -100, 100, 0)
        _press(row, Qt.Key.Key_Up, Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(row.value(), COARSE_STEP)
        _press(row, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
        self.assertEqual(row.value(), 0)


def _press(row: SliderRow, key: Qt.Key, modifiers: Qt.KeyboardModifier = Qt.KeyboardModifier.NoModifier) -> None:
    event = QKeyEvent(QKeyEvent.Type.KeyPress, int(key), modifiers)
    row._slider.keyPressEvent(event)


if __name__ == "__main__":
    unittest.main()
