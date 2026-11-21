from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.ui.density import Density


class ColorWheel(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title
        self.setFixedSize(Density.COLOR_WHEEL_WIDTH, Density.COLOR_WHEEL_HEIGHT)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        layout.addStretch()
        layout.addWidget(self._caption())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.setBrush(QColor(46, 46, 46))
        diameter = Density.COLOR_WHEEL_WIDTH - 20
        left = (Density.COLOR_WHEEL_WIDTH - diameter) // 2
        painter.drawEllipse(left, 4, diameter, diameter)
        center_x = Density.COLOR_WHEEL_WIDTH // 2
        center_y = 4 + diameter // 2
        painter.setPen(QPen(QColor(160, 160, 160), 1))
        painter.drawLine(center_x, 12, center_x, 4 + diameter - 8)
        painter.drawLine(left + 8, center_y, left + diameter - 8, center_y)
        painter.end()

    def _caption(self) -> QLabel:
        label = QLabel(self._title)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setWordWrap(False)
        label.setStyleSheet(f"font-size: {Density.HINT_PX}px; color: rgb(200, 200, 200);")
        return label
