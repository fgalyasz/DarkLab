from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class PresenceSettings:
    texture: int = 0
    clarity: int = 0
    dehaze: int = 0

    @property
    def is_neutral(self) -> bool:
        return self.texture == 0 and self.clarity == 0 and self.dehaze == 0

    @classmethod
    def from_tone(cls, tone: dict[str, int]) -> "PresenceSettings":
        return cls(tone.get("Texture", 0), tone.get("Clarity", 0), tone.get("Dehaze", 0))


def apply_presence(pixels: np.ndarray, settings: PresenceSettings) -> np.ndarray:
    if settings.is_neutral:
        return pixels
    values = pixels.astype(np.float32)
    values = _scaled_unsharp(values, 1.2, settings.clarity / 100.0)
    values = _scaled_unsharp(values, 0.6, settings.texture / 150.0)
    values = _dehazed(values, settings.dehaze / 100.0)
    return np.clip(values, 0, 255).astype(np.uint8)


def _scaled_unsharp(values: np.ndarray, radius: float, amount: float) -> np.ndarray:
    if amount == 0:
        return values
    blur = cv2.GaussianBlur(values, (0, 0), radius)
    return values + (values - blur) * amount


def _dehazed(values: np.ndarray, amount: float) -> np.ndarray:
    if amount == 0:
        return values
    luma = values @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    lifted = luma[..., None] + (values - luma[..., None]) * (1.0 + amount * 0.35)
    return lifted + amount * 12.0
