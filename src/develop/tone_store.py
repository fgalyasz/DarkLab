from __future__ import annotations

from pathlib import Path

from src.catalog.develop_settings import merge_develop_settings, read_develop_settings
from src.develop.tone_settings import decode_tone, encode_tone


def save_tone(catalog: Path, photo_id: int, values: dict[str, int]) -> None:
    merge_develop_settings(catalog, photo_id, encode_tone(values))


def load_tone(catalog: Path, photo_id: int) -> dict[str, int]:
    return decode_tone(read_develop_settings(catalog, photo_id))
