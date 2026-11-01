from __future__ import annotations

from src.develop.tone_settings import NEUTRAL_TEMPERATURE

AS_SHOT = "As Shot"
AUTO = "Auto"
CUSTOM = "Custom"
PRESET_VALUES = {
    AS_SHOT: (NEUTRAL_TEMPERATURE, 0),
    "Daylight": (5500, 0),
    "Cloudy": (6500, 10),
    "Shade": (7500, 10),
    "Tungsten": (2850, 0),
    "Fluorescent": (3800, 21),
    "Flash": (5500, 0),
}
CHOICES = (AS_SHOT, AUTO, *tuple(name for name in PRESET_VALUES if name != AS_SHOT), CUSTOM)


def choice_for(temperature: int, tint: int) -> str:
    if (temperature, tint) == PRESET_VALUES[AS_SHOT]:
        return AS_SHOT
    return CUSTOM
