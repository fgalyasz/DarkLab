from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPolygon
from PyQt6.QtWidgets import QWidget

BIN_COUNT = 64


def empty_channel() -> list[int]:
    return [0] * BIN_COUNT


def bin_index(channel: int) -> int:
    return min(BIN_COUNT - 1, max(0, channel) * BIN_COUNT // 256)


def add_rgb_sample(bins: tuple[list[int], list[int], list[int]], red: int, green: int, blue: int) -> None:
    bins[0][bin_index(red)] += 1
    bins[1][bin_index(green)] += 1
    bins[2][bin_index(blue)] += 1


def bins_from_image(image: QImage) -> tuple[list[int], list[int], list[int]]:
    bins = (empty_channel(), empty_channel(), empty_channel())
    if image.isNull():
        return bins
    _collect_samples(image, bins)
    return bins


class HistogramWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._bins = (empty_channel(), empty_channel(), empty_channel())
        self.setMinimumHeight(110)
        self.setMaximumHeight(130)

    def set_image(self, image: QImage) -> None:
        self._bins = bins_from_image(image)
        self.update()

    def clear_histogram(self) -> None:
        self._bins = (empty_channel(), empty_channel(), empty_channel())
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(28, 28, 28))
        self._paint_channel(painter, self._bins[0], QColor(180, 50, 50, 160))
        self._paint_channel(painter, self._bins[1], QColor(50, 160, 70, 140))
        self._paint_channel(painter, self._bins[2], QColor(60, 110, 200, 140))
        painter.end()

    def _paint_channel(self, painter: QPainter, values: list[int], color: QColor) -> None:
        peak = max(values) if any(values) else 1
        polygon = QPolygon(self._channel_points(values, peak))
        painter.setPen(QPen(color, 1))
        painter.setBrush(color)
        painter.drawPolygon(polygon)

    def _channel_points(self, values: list[int], peak: int) -> list[QPoint]:
        width = max(1, self.width() - 8)
        height = max(1, self.height() - 8)
        points = [QPoint(4, self.height() - 4)]
        points.extend(self._curve_points(values, peak, width, height))
        points.append(QPoint(4 + width, self.height() - 4))
        return points

    def _curve_points(self, values: list[int], peak: int, width: int, height: int) -> list[QPoint]:
        points: list[QPoint] = []
        last = len(values) - 1
        for index, value in enumerate(values):
            x = 4 + int(index / max(1, last) * width)
            y = self.height() - 4 - int(value / peak * height)
            points.append(QPoint(x, y))
        return points


def _collect_samples(image: QImage, bins: tuple[list[int], list[int], list[int]]) -> None:
    step = _sample_step(image)
    for y in range(0, image.height(), step):
        _sample_row(image, bins, y, step)


def _sample_step(image: QImage) -> int:
    area = max(1, image.width() * image.height())
    return max(1, int(area ** 0.5 / 48))


def _sample_row(image: QImage, bins: tuple[list[int], list[int], list[int]], y: int, step: int) -> None:
    for x in range(0, image.width(), step):
        color = image.pixelColor(x, y)
        add_rgb_sample(bins, color.red(), color.green(), color.blue())
