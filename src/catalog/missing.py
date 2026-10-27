from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.catalog.file_hash import content_hash
from src.catalog.index_images import index_image_path
from src.catalog.locations import database_file

logger = logging.getLogger(__name__)

ALL_PHOTOS = "SELECT id, original_path, content_hash FROM photos ORDER BY id"
READ_PHOTO = "SELECT original_path, content_hash FROM photos WHERE id = ?"
WRITE_LINK = "UPDATE photos SET original_path = ?, content_hash = ? WHERE id = ?"


class RelinkError(ValueError):
    pass


@dataclass(frozen=True)
class MissingPhoto:
    photo_id: int
    original: Path


def missing_photos(catalog: Path) -> list[MissingPhoto]:
    found = [MissingPhoto(int(row[0]), Path(str(row[1]))) for row in _all_rows(catalog)]
    missing = [photo for photo in found if not photo.original.is_file()]
    for photo in missing:
        logger.debug("Original is missing for photo %s: %s", photo.photo_id, photo.original)
    return missing


def missing_index_paths(catalog: Path) -> set[Path]:
    return {index_image_path(catalog, photo.photo_id) for photo in missing_photos(catalog)}


def is_missing(catalog: Path, photo_id: int) -> bool:
    original = _stored_link(catalog, photo_id)[0]
    return not original.is_file()


def relink_photo(catalog: Path, photo_id: int, replacement: Path, confirm_different: bool = False) -> None:
    if not replacement.is_file():
        raise RelinkError(f"Replacement is not a file: {replacement}")
    digest = content_hash(replacement)
    _require_same_content(catalog, photo_id, replacement, digest, confirm_different)
    _write_link(catalog, photo_id, replacement, digest)


def _all_rows(catalog: Path) -> list[tuple[object, ...]]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        return connection.execute(ALL_PHOTOS).fetchall()
    finally:
        connection.close()


def _stored_link(catalog: Path, photo_id: int) -> tuple[Path, str | None]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        row = connection.execute(READ_PHOTO, (photo_id,)).fetchone()
    finally:
        connection.close()
    if row is None:
        raise RelinkError(f"No photo {photo_id} in catalog {catalog}")
    return Path(str(row[0])), None if row[1] is None else str(row[1])


def _require_same_content(
    catalog: Path, photo_id: int, replacement: Path, digest: str, confirm_different: bool
) -> None:
    stored = _stored_link(catalog, photo_id)[1]
    if stored is None or stored == digest or confirm_different:
        return
    raise RelinkError(f"Content of {replacement} differs from photo {photo_id}; confirm to relink")


def _write_link(catalog: Path, photo_id: int, replacement: Path, digest: str) -> None:
    connection = sqlite3.connect(database_file(catalog))
    try:
        connection.execute(WRITE_LINK, (str(replacement), digest, photo_id))
        connection.commit()
    finally:
        connection.close()
