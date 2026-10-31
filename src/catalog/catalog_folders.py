from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.catalog.file_hash import content_hash
from src.catalog.locations import database_file
from src.catalog.missing import RelinkError

logger = logging.getLogger(__name__)

PHOTO_ORIGINALS = "SELECT id, original_path, content_hash FROM photos ORDER BY id"
WRITE_PATH = "UPDATE photos SET original_path = ?, content_hash = ? WHERE id = ?"


@dataclass(frozen=True)
class CatalogFolder:
    path: Path
    photo_ids: tuple[int, ...]
    is_missing: bool


@dataclass(frozen=True)
class _StoredPhoto:
    photo_id: int
    original: Path
    digest: str | None


def catalog_folders(catalog: Path) -> list[CatalogFolder]:
    grouped: dict[Path, list[int]] = {}
    for photo in _stored_photos(catalog):
        grouped.setdefault(photo.original.parent, []).append(photo.photo_id)
    return [_folder(path, grouped[path]) for path in sorted(grouped, key=str)]


def folder_photo_ids(catalog: Path, folder: Path) -> tuple[int, ...]:
    return tuple(photo.photo_id for photo in _stored_photos(catalog) if photo.original.parent == folder)


def relink_folder(catalog: Path, folder: Path, replacement: Path, confirm_different: bool = False) -> int:
    if not replacement.is_dir():
        raise RelinkError(f"Replacement is not a directory: {replacement}")
    photos = [photo for photo in _stored_photos(catalog) if photo.original.parent == folder]
    if not photos:
        raise RelinkError(f"No photos of folder {folder} in catalog {catalog}")
    links = [_checked_link(photo, replacement, confirm_different) for photo in photos]
    _write_links(catalog, links)
    logger.info("Relinked folder %s to %s: %s photos", folder, replacement, len(links))
    return len(links)


def _folder(path: Path, photo_ids: list[int]) -> CatalogFolder:
    return CatalogFolder(path, tuple(photo_ids), not path.is_dir())


def _stored_photos(catalog: Path) -> list[_StoredPhoto]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        rows = connection.execute(PHOTO_ORIGINALS).fetchall()
    finally:
        connection.close()
    return [_StoredPhoto(int(row[0]), Path(str(row[1])), _digest(row[2])) for row in rows]


def _digest(value: object) -> str | None:
    return None if value is None else str(value)


def _checked_link(photo: _StoredPhoto, replacement: Path, confirm_different: bool) -> tuple[int, Path, str]:
    target = replacement / photo.original.name
    if not target.is_file():
        raise RelinkError(f"Replacement folder has no {photo.original.name}: {replacement}")
    digest = content_hash(target)
    if photo.digest not in (None, digest) and not confirm_different:
        raise RelinkError(f"Content of {target} differs from photo {photo.photo_id}; confirm to relink")
    return photo.photo_id, target, digest


def _write_links(catalog: Path, links: list[tuple[int, Path, str]]) -> None:
    connection = sqlite3.connect(database_file(catalog))
    try:
        with connection:
            for photo_id, target, digest in links:
                connection.execute(WRITE_PATH, (str(target), digest, photo_id))
    finally:
        connection.close()
