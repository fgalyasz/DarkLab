from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QLinearGradient, QMouseEvent, QPainter, QPen, QPolygon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QSlider, QWidget

from src.ui.density import Density
from src.ui.widgets.slider_geometry import (
    POINTER_HALF_WIDTH, format_slider_value, handle_center_x, pointer_polygon, tick_positions, value_ratio,
)

SLIDER_ROW_HEIGHT = 20
SLIDER_WIDGET_HEIGHT = 18
FINE_STEP = 1
COARSE_STEP = 10
GROOVE_TOP = 6
GROOVE_HEIGHT = 4
TICK_MAJOR_COLOR = QColor(40, 40, 40)
TICK_MINOR_COLOR = QColor(56, 56, 56)
GROOVE_BORDER = QColor(24, 24, 24)
GROOVE_BEVEL = QColor(92, 92, 92)
POINTER_OUTLINE = QColor(22, 22, 22)


class DevelopSlider(QSlider):
    reset_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(Qt.Orientation.Horizontal)
        self._hovered = False
        self._pressed = False
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSingleStep(FINE_STEP)
        self.setPageStep(COARSE_STEP)
        self.setFixedHeight(SLIDER_WIDGET_HEIGHT)

    def enterEvent(self, event) -> None:
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.setValue(self._value_at_x(event.position().x()))
            self.update()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._pressed:
            self.setValue(self._value_at_x(event.position().x()))
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._pressed and event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self.update()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self.reset_requested.emit()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        step = _key_step(event)
        if step is None:
            super().keyPressEvent(event)
            return
        self.setValue(self.value() + step)
        event.accept()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        left, right = self._track_bounds()
        _paint_ticks(painter, left, right)
        _paint_groove(painter, left, right)
        ratio = value_ratio(self.value(), self.minimum(), self.maximum())
        cx = handle_center_x(ratio, left, right)
        _paint_pointer(painter, cx, self._hovered, self._pressed or self.hasFocus())
        painter.end()

    def _track_bounds(self) -> tuple[int, int]:
        pad = POINTER_HALF_WIDTH + 1
        return pad, max(pad, self.width() - pad - 1)

    def _value_at_x(self, x: float) -> int:
        left, right = self._track_bounds()
        span = max(1, right - left)
        ratio = max(0.0, min(1.0, (x - left) / span))
        return round(self.minimum() + ratio * (self.maximum() - self.minimum()))


class SliderRow(QWidget):
    changed = pyqtSignal(int)

    def __init__(self, title: str, minimum: int, maximum: int, value: int = 0) -> None:
        super().__init__()
        self.setObjectName("developRow")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(SLIDER_ROW_HEIGHT)
        self.title = title
        self._minimum = minimum
        self._default = value
        self._slider = DevelopSlider()
        self._value_label = QLabel()
        self._build(title, minimum, maximum, value)

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, value: int) -> None:
        self._slider.setValue(value)

    @property
    def default(self) -> int:
        return self._default

    def reset(self) -> None:
        self._slider.setValue(self._default)

    def set_compact_caption(self, width: int) -> None:
        caption = self.findChild(QLabel, "sliderCaption")
        if caption is not None:
            caption.setFixedWidth(width)
            caption.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

    def _build(self, title: str, minimum: int, maximum: int, value: int) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(Density.SLIDER_ROW_MARGIN_X, 0, Density.SLIDER_ROW_MARGIN_X, 0)
        row.setSpacing(Density.SLIDER_ROW_SPACING)
        row.addWidget(self._caption(title))
        self._configure_slider(minimum, maximum, value)
        row.addWidget(self._slider, 1)
        self._configure_value_label()
        row.addWidget(self._value_label)
        self._show_value(value)

    def _configure_slider(self, minimum: int, maximum: int, value: int) -> None:
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(value)
        self._slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._slider.valueChanged.connect(self._on_changed)
        self._slider.reset_requested.connect(self.reset)

    def _caption(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sliderCaption")
        label.setFixedWidth(Density.SLIDER_CAPTION_WIDTH)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        label.setTextFormat(Qt.TextFormat.PlainText)
        _apply_single_line(label)
        return label

    def _configure_value_label(self) -> None:
        self._value_label.setObjectName("sliderValue")
        self._value_label.setFixedWidth(Density.SLIDER_VALUE_WIDTH)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        _apply_single_line(self._value_label)

    def _on_changed(self, value: int) -> None:
        self._show_value(value)
        self.changed.emit(value)

    def _show_value(self, value: int) -> None:
        self._value_label.setText(format_slider_value(self.title, value, self._minimum))


def _paint_ticks(painter: QPainter, left: int, right: int) -> None:
    for x, is_major in tick_positions(left, right):
        height = 3 if is_major else 2
        color = TICK_MAJOR_COLOR if is_major else TICK_MINOR_COLOR
        painter.fillRect(x, GROOVE_TOP - height - 1, 1, height, color)


def _paint_groove(painter: QPainter, left: int, right: int) -> None:
    width = max(1, right - left + 1)
    gradient = QLinearGradient(left, 0, right, 0)
    gradient.setColorAt(0.0, QColor(48, 48, 48))
    gradient.setColorAt(0.5, QColor(68, 68, 68))
    gradient.setColorAt(1.0, QColor(86, 86, 86))
    painter.fillRect(QRect(left, GROOVE_TOP, width, GROOVE_HEIGHT), gradient)
    painter.setPen(QPen(GROOVE_BORDER, 1))
    painter.drawRect(left, GROOVE_TOP, width - 1, GROOVE_HEIGHT - 1)
    painter.fillRect(left, GROOVE_TOP + GROOVE_HEIGHT, width, 1, GROOVE_BEVEL)


def _paint_pointer(painter: QPainter, cx: int, hovered: bool, active: bool) -> None:
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    top_y = GROOVE_TOP - 1
    points = [QPoint(x, y) for x, y in pointer_polygon(cx, top_y)]
    gradient = _pointer_gradient(top_y, hovered, active)
    painter.setBrush(gradient)
    painter.setPen(QPen(POINTER_OUTLINE, 1))
    painter.drawPolygon(QPolygon(points))


def _pointer_gradient(top_y: int, hovered: bool, active: bool) -> QLinearGradient:
    gradient = QLinearGradient(0, top_y, 0, top_y + 9)
    top, bottom = _pointer_colors(hovered, active)
    gradient.setColorAt(0.0, top)
    gradient.setColorAt(1.0, bottom)
    return gradient


def _pointer_colors(hovered: bool, active: bool) -> tuple[QColor, QColor]:
    if active:
        return QColor(232, 232, 232), QColor(186, 186, 186)
    if hovered:
        return QColor(212, 212, 212), QColor(164, 164, 164)
    return QColor(186, 186, 186), QColor(138, 138, 138)


def _key_step(event: QKeyEvent) -> int | None:
    step = COARSE_STEP if event.modifiers() & Qt.KeyboardModifier.ShiftModifier else FINE_STEP
    if event.key() in (Qt.Key.Key_Left, Qt.Key.Key_Down):
        return -step
    if event.key() in (Qt.Key.Key_Right, Qt.Key.Key_Up):
        return step
    return None


def _apply_single_line(label: QLabel) -> None:
    label.setWordWrap(False)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
