from __future__ import annotations

import logging
from pathlib import Path

from src.catalog.index_images import delete_index_image
from src.catalog.photos import forget_photo, photo_original

logger = logging.getLogger(__name__)


def photo_id_of_index(path: Path) -> int | None:
    if path.suffix.lower() != ".jpg" or not path.stem.isdigit():
        return None
    photo_id = int(path.stem)
    if photo_id < 1:
        return None
    return photo_id


def remove_indexes(catalog: Path, photo_ids: list[int], delete_original: bool) -> int:
    removed = [_remove_one(catalog, photo_id, delete_original) for photo_id in photo_ids]
    return sum(removed)


def remove_catalog_photo(catalog: Path, photo_id: int, delete_original: bool) -> None:
    original = photo_original(catalog, photo_id)
    if delete_original:
        _unlink_file(original)
    delete_index_image(catalog, photo_id)
    forget_photo(catalog, photo_id)


def _remove_one(catalog: Path, photo_id: int, delete_original: bool) -> int:
    try:
        remove_catalog_photo(catalog, photo_id, delete_original)
    except OSError as error:
        logger.error("Could not remove photo %s: %s", photo_id, error)
        return 0
    return 1


def _unlink_file(path: Path | None) -> None:
    if path is None or not path.is_file():
        return
    path.unlink()
