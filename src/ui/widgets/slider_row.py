from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSlider, QWidget


class SliderRow(QWidget):
    changed = pyqtSignal(int)

    def __init__(self, title: str, minimum: int, maximum: int, value: int = 0) -> None:
        super().__init__()
        self.setObjectName("developRow")
        self.title = title
        self._default = value
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._value_label = QLabel()
        self._build(title, minimum, maximum, value)

    def value(self) -> int:
        return self._slider.value()

    def set_value(self, value: int) -> None:
        self._slider.setValue(value)

    def reset(self) -> None:
        self._slider.setValue(self._default)

    def _build(self, title: str, minimum: int, maximum: int, value: int) -> None:
        row = QHBoxLayout(self)
        row.setContentsMargins(4, 0, 4, 0)
        row.setSpacing(6)
        row.addWidget(self._caption(title))
        self._slider.setRange(minimum, maximum)
        self._slider.setValue(value)
        self._slider.valueChanged.connect(self._on_changed)
        row.addWidget(self._slider, 1)
        self._value_label.setMinimumWidth(42)
        self._value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(self._value_label)
        self._show_value(value)

    def _caption(self, title: str) -> QLabel:
        label = QLabel(title)
        label.setMinimumWidth(72)
        return label

    def _on_changed(self, value: int) -> None:
        self._show_value(value)
        self.changed.emit(value)

    def _show_value(self, value: int) -> None:
        if self.title == "Exposure":
            self._value_label.setText(f"{value / 100:+.2f}")
            return
        self._value_label.setText(str(value))
