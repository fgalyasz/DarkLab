from __future__ import annotations

from dataclasses import dataclass

import numpy as np

LUMA = np.array([0.299, 0.587, 0.114], dtype=np.float32)


@dataclass(frozen=True)
class BasicTone:
    highlights: int = 0
    shadows: int = 0
    whites: int = 0
    blacks: int = 0

    @property
    def is_neutral(self) -> bool:
        return self == BasicTone()

    @classmethod
    def from_tone(cls, tone: dict[str, int]) -> "BasicTone":
        return cls(
            tone.get("Highlights", 0),
            tone.get("Shadows", 0),
            tone.get("Whites", 0),
            tone.get("Blacks", 0),
        )


def apply_basic_tone(pixels: np.ndarray, tone: BasicTone) -> np.ndarray:
    if tone.is_neutral:
        return pixels
    values = pixels.astype(np.float32) / 255.0
    luma = values @ LUMA
    values = _shift_zone(values, luma, tone.shadows / 100.0, dark=True, power=2.0, strength=0.35)
    values = _shift_zone(values, luma, tone.highlights / 100.0, dark=False, power=2.0, strength=0.35)
    values = _shift_zone(values, luma, tone.blacks / 100.0, dark=True, power=3.0, strength=0.22)
    values = _shift_zone(values, luma, tone.whites / 100.0, dark=False, power=3.0, strength=0.22)
    return np.clip(values * 255.0, 0, 255).astype(np.uint8)


def _shift_zone(
    values: np.ndarray,
    luma: np.ndarray,
    amount: float,
    dark: bool,
    power: float,
    strength: float,
) -> np.ndarray:
    if amount == 0:
        return values
    weight = ((1.0 - luma) if dark else luma) ** power
    return values + amount * strength * weight[..., None]
