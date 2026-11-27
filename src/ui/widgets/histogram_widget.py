from PyQt6.QtCore import QPoint, QRect
from PyQt6.QtGui import QColor, QImage, QPainter, QPen, QPolygon
from PyQt6.QtWidgets import QWidget

BIN_COUNT = 64
PAD = 6
SURFACE = QColor(80, 80, 80)
WELL_FILL = QColor(60, 60, 60)
WELL_BORDER = QColor(24, 24, 24)


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
        painter.fillRect(self.rect(), SURFACE)
        well = self._well_rect()
        painter.fillRect(well, WELL_FILL)
        painter.setPen(QPen(WELL_BORDER, 1))
        painter.drawRect(well.adjusted(0, 0, -1, -1))
        self._paint_channels(painter, well)
        painter.end()

    def _well_rect(self) -> QRect:
        return self.rect().adjusted(PAD, PAD, -PAD, -PAD)

    def _paint_channels(self, painter: QPainter, well: QRect) -> None:
        self._paint_channel(painter, well, self._bins[0], QColor(180, 50, 50, 160))
        self._paint_channel(painter, well, self._bins[1], QColor(50, 160, 70, 140))
        self._paint_channel(painter, well, self._bins[2], QColor(60, 110, 200, 140))

    def _paint_channel(self, painter: QPainter, well: QRect, values: list[int], color: QColor) -> None:
        if not any(values):
            return
        peak = max(values)
        polygon = QPolygon(self._channel_points(well, values, peak))
        painter.setPen(QPen(color, 1))
        painter.setBrush(color)
        painter.drawPolygon(polygon)

    def _channel_points(self, well: QRect, values: list[int], peak: int) -> list[QPoint]:
        inner = well.adjusted(2, 2, -2, -2)
        points = [QPoint(inner.left(), inner.bottom())]
        points.extend(self._curve_points(inner, values, peak))
        points.append(QPoint(inner.right(), inner.bottom()))
        return points

    def _curve_points(self, inner: QRect, values: list[int], peak: int) -> list[QPoint]:
        points: list[QPoint] = []
        last = max(1, len(values) - 1)
        for index, value in enumerate(values):
            x = inner.left() + int(index / last * max(1, inner.width()))
            y = inner.bottom() - int(value / peak * max(1, inner.height()))
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
