from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class ToneCurveWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setMinimumHeight(150)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(32, 32, 32))
        self._draw_grid(painter)
        self._draw_curve(painter)
        painter.end()

    def _draw_grid(self, painter: QPainter) -> None:
        painter.setPen(QPen(QColor(70, 70, 70), 1))
        bounds = self.rect().adjusted(8, 8, -8, -8)
        painter.drawRect(bounds)
        painter.drawLine(bounds.topLeft(), bounds.bottomRight())

    def _draw_curve(self, painter: QPainter) -> None:
        bounds = self.rect().adjusted(8, 8, -8, -8)
        painter.setPen(QPen(QColor(230, 230, 230), 2))
        painter.drawLine(QPoint(bounds.left(), bounds.bottom()), QPoint(bounds.right(), bounds.top()))
