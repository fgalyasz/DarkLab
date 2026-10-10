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


def delete_index_image(catalog: Path, photo_id: int) -> None:
    _require_photo_id(photo_id)
    path = index_image_path(catalog, photo_id)
    if path.is_file():
        path.unlink()


def list_index_images(catalog: Path) -> list[Path]:
    folder = preview_directory(catalog)
    if not folder.is_dir():
        return []
    return _sorted_indexes(folder)


def _sorted_indexes(folder: Path) -> list[Path]:
    found = [path for path in folder.iterdir() if _is_index_file(path)]
    return sorted(found, key=_index_id)


def _is_index_file(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() != ".jpg":
        return False
    return path.stem.isdigit() and int(path.stem) > 0


def _index_id(path: Path) -> int:
    return int(path.stem)


def _require_photo_id(photo_id: int) -> None:
    if photo_id < 1:
        raise ValueError("Photo id must be positive")
