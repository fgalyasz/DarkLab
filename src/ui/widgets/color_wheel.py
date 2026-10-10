from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ColorWheel(QWidget):
    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title
        self.setFixedSize(108, 128)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch()
        layout.addWidget(self._caption())

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(90, 90, 90), 1))
        painter.setBrush(QColor(46, 46, 46))
        painter.drawEllipse(18, 8, 72, 72)
        painter.setPen(QPen(QColor(160, 160, 160), 1))
        painter.drawLine(54, 20, 54, 68)
        painter.drawLine(30, 44, 78, 44)
        painter.end()

    def _caption(self) -> QLabel:
        label = QLabel(self._title)
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        return label
