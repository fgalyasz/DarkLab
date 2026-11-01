from __future__ import annotations

from typing import Callable

from PyQt6.QtGui import QImage

from src.develop.tone_settings import BALANCE_KEYS
from src.develop.white_balance import AUTO, CUSTOM, PRESET_VALUES, choice_for
from src.imaging.color_grade import auto_balance
from src.ui.develop_sections import DevelopControls
from src.ui.preview_image import average_rgb


class WhiteBalanceBinding:
    def __init__(self, controls: DevelopControls, source: Callable[[], QImage]) -> None:
        self._controls = controls
        self._source = source
        self._busy = False
        controls.white_balance.activated.connect(self._chosen)
        for row in self._sliders():
            row.changed.connect(self._slider_edited)

    def show_choice(self) -> None:
        temperature, tint = self._values()
        self._select(choice_for(temperature, tint))

    def _sliders(self) -> list:
        return self._controls.first_named(BALANCE_KEYS)

    def _values(self) -> tuple[int, int]:
        values = self._controls.named_values(BALANCE_KEYS)
        return values["Temp"], values["Tint"]

    def _chosen(self, _index: int) -> None:
        name = self._controls.white_balance.currentText()
        if name == CUSTOM:
            return
        temperature, tint = self._auto_values() if name == AUTO else PRESET_VALUES[name]
        self._write(temperature, tint)
        self._select(name)

    def _auto_values(self) -> tuple[int, int]:
        return auto_balance(average_rgb(self._source()))

    def _write(self, temperature: int, tint: int) -> None:
        self._busy = True
        try:
            self._controls.restore_named(BALANCE_KEYS, {"Temp": temperature, "Tint": tint})
        finally:
            self._busy = False

    def _slider_edited(self, _value: int) -> None:
        if not self._busy:
            self.show_choice()

    def _select(self, name: str) -> None:
        self._controls.white_balance.setCurrentText(name)
