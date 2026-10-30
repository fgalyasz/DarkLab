from __future__ import annotations

from dataclasses import dataclass

EDGE_KEYS = ("CropLeft", "CropTop", "CropRight", "CropBottom")
ANGLE_KEY = "CropAngle"
LOCK_KEY = "CropAspectLock"
CROP_KEYS = EDGE_KEYS + (ANGLE_KEY,)
MAX_EDGE = 90
MAX_ANGLE = 45


@dataclass(frozen=True)
class CropSettings:
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0
    angle: int = 0
    locked: bool = False

    @property
    def is_empty(self) -> bool:
        return not any((self.left, self.top, self.right, self.bottom, self.angle))


def encode_crop(crop: CropSettings) -> dict[str, str]:
    values = (crop.left, crop.top, crop.right, crop.bottom, crop.angle)
    encoded = {key: str(value) for key, value in zip(CROP_KEYS, values)}
    return {**encoded, LOCK_KEY: "1" if crop.locked else "0"}


def decode_crop(settings: dict[str, str]) -> CropSettings:
    edges = [_whole_number(settings.get(key)) for key in EDGE_KEYS]
    angle = _whole_number(settings.get(ANGLE_KEY))
    return CropSettings(*edges, angle, settings.get(LOCK_KEY) == "1")


def crop_box(size: tuple[int, int], crop: CropSettings) -> tuple[int, int, int, int]:
    width, height = size
    left, right = _span(width, crop.left, crop.right)
    top, bottom = _span(height, crop.top, crop.bottom)
    return (left, top, right, bottom)


def lock_edges(crop: CropSettings, changed: str) -> CropSettings:
    if not crop.locked:
        return crop
    if changed in ("CropLeft", "CropRight"):
        return _with_vertical_total(crop, crop.left + crop.right)
    return _with_horizontal_total(crop, crop.top + crop.bottom)


def _with_vertical_total(crop: CropSettings, total: int) -> CropSettings:
    bottom = _clamped_edge(total - crop.top)
    return CropSettings(crop.left, crop.top, crop.right, bottom, crop.angle, crop.locked)


def _with_horizontal_total(crop: CropSettings, total: int) -> CropSettings:
    right = _clamped_edge(total - crop.left)
    return CropSettings(crop.left, crop.top, right, crop.bottom, crop.angle, crop.locked)


def _clamped_edge(value: int) -> int:
    return max(0, min(MAX_EDGE, value))


def _span(length: int, start_percent: int, end_percent: int) -> tuple[int, int]:
    start = min(round(length * start_percent / 100), length - 1)
    end = max(length - round(length * end_percent / 100), start + 1)
    return (start, min(end, length))


def _whole_number(raw: str | None) -> int:
    try:
        return int(raw) if raw is not None else 0
    except ValueError:
        return 0
