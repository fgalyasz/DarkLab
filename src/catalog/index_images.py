from __future__ import annotations

from pathlib import Path

from src.catalog.locations import preview_directory


def write_index_image(catalog: Path, photo_id: int, content: bytes) -> Path:
    _require_photo_id(photo_id)
    destination = index_image_path(catalog, photo_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination


def read_index_image(catalog: Path, photo_id: int) -> bytes | None:
    path = index_image_path(catalog, photo_id)
    if not path.is_file():
        return None
    return path.read_bytes()


def index_image_path(catalog: Path, photo_id: int) -> Path:
    return preview_directory(catalog) / f"{photo_id}.jpg"


def _require_photo_id(photo_id: int) -> None:
    if photo_id < 1:
        raise ValueError("Photo id must be positive")
