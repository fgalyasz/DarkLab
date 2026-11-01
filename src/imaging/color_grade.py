from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from src.develop.tone_settings import NEUTRAL_TEMPERATURE

TEMPERATURE_RANGE = (2000, 50000)
TINT_RANGE = (-150, 150)
TEMPERATURE_STRENGTH = 0.5
TINT_STRENGTH = 0.3
TINT_SPAN = 150
LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


@dataclass(frozen=True)
class ColorGrade:
    temperature: int = NEUTRAL_TEMPERATURE
    tint: int = 0
    vibrance: int = 0
    saturation: int = 0

    @property
    def is_neutral(self) -> bool:
        return self == ColorGrade()

    @classmethod
    def from_tone(cls, tone: dict[str, int]) -> "ColorGrade":
        return cls(
            tone.get("Temp", NEUTRAL_TEMPERATURE), tone.get("Tint", 0),
            tone.get("Vibrance", 0), tone.get("Saturation", 0),
        )


def channel_gains(temperature: int, tint: int) -> np.ndarray:
    shift = math.log2(temperature / NEUTRAL_TEMPERATURE) * TEMPERATURE_STRENGTH
    green = 2 ** (-tint / TINT_SPAN * TINT_STRENGTH)
    return np.array([2 ** shift, green, 2 ** -shift], dtype=np.float32)


def auto_balance(mean_rgb: tuple[float, float, float]) -> tuple[int, int]:
    red, green, blue = (max(channel, 1.0) for channel in mean_rgb)
    temperature = _clamped(NEUTRAL_TEMPERATURE * blue / red, TEMPERATURE_RANGE)
    shift = math.log2(temperature / NEUTRAL_TEMPERATURE) * TEMPERATURE_STRENGTH
    green_gain = red * 2 ** shift / green
    tint = -TINT_SPAN / TINT_STRENGTH * math.log2(green_gain)
    return temperature, _clamped(tint, TINT_RANGE)


def apply_grade(pixels: np.ndarray, grade: ColorGrade) -> np.ndarray:
    if grade.is_neutral:
        return pixels
    values = pixels.astype(np.float32) * channel_gains(grade.temperature, grade.tint)
    values = _saturated(values, grade)
    return np.clip(values, 0, 255).astype(np.uint8)


def _saturated(values: np.ndarray, grade: ColorGrade) -> np.ndarray:
    luma = (values @ LUMA)[..., None]
    factor = np.maximum(1.0 + grade.saturation / 100.0 + _vibrance_amount(values, grade.vibrance), 0.0)
    return luma + (values - luma) * factor


def _vibrance_amount(values: np.ndarray, vibrance: int) -> np.ndarray | float:
    if vibrance == 0:
        return 0.0
    top = values.max(axis=-1, keepdims=True)
    chroma = (top - values.min(axis=-1, keepdims=True)) / np.maximum(top, 1.0)
    return vibrance / 100.0 * (1.0 - np.clip(chroma, 0, 1))


def _clamped(value: float, limits: tuple[int, int]) -> int:
    return int(round(max(limits[0], min(limits[1], value))))
