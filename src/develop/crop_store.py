from __future__ import annotations

from pathlib import Path

from src.catalog.develop_settings import merge_develop_settings, read_develop_settings
from src.develop.crop_settings import CropSettings, decode_crop, encode_crop


def save_crop(catalog: Path, photo_id: int, crop: CropSettings) -> None:
    merge_develop_settings(catalog, photo_id, encode_crop(crop))


def load_crop(catalog: Path, photo_id: int) -> CropSettings:
    return decode_crop(read_develop_settings(catalog, photo_id))
