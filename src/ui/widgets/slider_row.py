from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizePolicy, QSlider, QWidget

from src.ui.density import Density

SLIDER_ROW_HEIGHT = 16
FINE_STEP = 1
COARSE_STEP = 10


class DevelopSlider(QSlider):
    reset_requested = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(Qt.Orientation.Horizontal)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSingleStep(FINE_STEP)
        self.setPageStep(COARSE_STEP)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        self.setFocus(Qt.FocusReason.MouseFocusReason)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
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


class SliderRow(QWidget):
    changed = pyqtSignal(int)

    def __init__(self, title: str, minimum: int, maximum: int, value: int = 0) -> None:
        super().__init__()
        self.setObjectName("developRow")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(SLIDER_ROW_HEIGHT)
        self.title = title
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

    def _build(self, title: str, minimum: int, maximum: int, value: int) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(2, 0, 2, 0)
        row.setSpacing(4)
        row.addWidget(self._caption(title))
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(value)
        self._slider.setFixedHeight(12)
        self._slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._slider.valueChanged.connect(self._on_changed)
        self._slider.reset_requested.connect(self.reset)
        row.addWidget(self._slider, 1)
        self._configure_value_label()
        row.addWidget(self._value_label)
        self._show_value(value)

    def _caption(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setObjectName("sliderCaption")
        label.setFixedWidth(Density.SLIDER_CAPTION_WIDTH)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
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
        if self.title == "Exposure":
            self._value_label.setText(f"{value / 100:+.2f}")
            return
        self._value_label.setText(str(value))


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
