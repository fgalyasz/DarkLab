from __future__ import annotations

import re
from dataclasses import dataclass

from src.develop.crop_settings import LOCK_KEY, CropSettings, encode_crop
from src.develop.tone_settings import TONE_KEYS, encode_tone

IMPORT_LABEL = "Import"
SAVED_LABEL = "Saved settings"


@dataclass(frozen=True)
class HistoryStep:
    label: str
    settings: dict[str, str]


def develop_settings(tone: dict[str, int], crop: CropSettings) -> dict[str, str]:
    return {**encode_tone(tone), **encode_crop(crop)}


def import_settings() -> dict[str, str]:
    return develop_settings({key: 0 for key in TONE_KEYS}, CropSettings())


def step_label(before: dict[str, str], after: dict[str, str]) -> str:
    changed = sorted(key for key in after if before.get(key) != after[key])
    if len(changed) == 1:
        return _single_label(changed[0], after[changed[0]])
    return "Crop" if changed and all(key.startswith("Crop") for key in changed) else f"{len(changed)} settings"


def _single_label(key: str, value: str) -> str:
    name = re.sub(r"(?<!^)(?=[A-Z])", " ", key)
    if key == LOCK_KEY:
        return f"{name} {'on' if value == '1' else 'off'}"
    return f"{name} {value}"


class DevelopHistory:
    def __init__(self, start: dict[str, str]) -> None:
        self._steps = [HistoryStep(IMPORT_LABEL, start)]
        self._current = 0

    @property
    def steps(self) -> list[HistoryStep]:
        return list(self._steps)

    @property
    def current_index(self) -> int:
        return self._current

    @property
    def import_step(self) -> HistoryStep:
        return self._steps[0]

    def current_settings(self) -> dict[str, str]:
        return self._steps[self._current].settings

    def record(self, settings: dict[str, str], label: str | None = None) -> bool:
        if settings == self.current_settings():
            return False
        text = label or step_label(self.current_settings(), settings)
        del self._steps[self._current + 1:]
        self._steps.append(HistoryStep(text, settings))
        self._current = len(self._steps) - 1
        return True

    def select(self, index: int) -> dict[str, str]:
        if not 0 <= index < len(self._steps):
            raise IndexError(f"No History Step {index}")
        self._current = index
        return self._steps[index].settings
