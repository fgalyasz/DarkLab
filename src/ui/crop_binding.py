from __future__ import annotations

from functools import partial
from typing import Callable

from src.develop.crop_settings import CropSettings, lock_edges
from src.ui.develop_sections import DevelopControls

TITLE_KEYS = {
    "Left": "CropLeft",
    "Top": "CropTop",
    "Right": "CropRight",
    "Bottom": "CropBottom",
    "Angle": "CropAngle",
}


class CropBinding:
    def __init__(self, controls: DevelopControls, on_change: Callable[[], None]) -> None:
        self._controls = controls
        self._on_change = on_change
        self._busy = False
        self._connect_sliders()
        controls.crop_lock.toggled.connect(partial(self._edited, "CropAspectLock"))

    def read(self) -> CropSettings:
        values = {row.title: row.value() for row in self._controls.sliders if row.title in TITLE_KEYS}
        locked = self._controls.crop_lock.isChecked()
        return CropSettings(values["Left"], values["Top"], values["Right"], values["Bottom"], values["Angle"], locked)

    def write(self, crop: CropSettings) -> None:
        self._busy = True
        try:
            self._set_controls(crop)
        finally:
            self._busy = False

    def _connect_sliders(self) -> None:
        for row in self._controls.sliders:
            if row.title in TITLE_KEYS:
                row.changed.connect(partial(self._edited, TITLE_KEYS[row.title]))

    def _set_controls(self, crop: CropSettings) -> None:
        shown = {"Left": crop.left, "Top": crop.top, "Right": crop.right, "Bottom": crop.bottom, "Angle": crop.angle}
        for row in self._controls.sliders:
            if row.title in shown:
                row.set_value(shown[row.title])
        self._controls.crop_lock.setChecked(crop.locked)

    def _edited(self, key: str, _value: object = None) -> None:
        if self._busy:
            return
        self.write(lock_edges(self.read(), key))
        self._on_change()
