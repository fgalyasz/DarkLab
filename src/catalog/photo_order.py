from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import exifread

from src.catalog.locations import database_file
from src.catalog.removal import photo_id_of_index

CAPTURE = "capture"
NAME = "name"
IMPORTED = "imported"
RATING = "rating"
SORT_MODES = (CAPTURE, NAME, IMPORTED, RATING)
ORIGINALS = "SELECT id, original_path FROM photos ORDER BY id"
CAPTURE_TAG = "EXIF DateTimeOriginal"
CAPTURE_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class SortKeys:
    names: dict[int, str] = field(default_factory=dict)
    captures: dict[int, float | None] = field(default_factory=dict)


def read_sort_keys(catalog: Path) -> SortKeys:
    originals = {photo_id: original for photo_id, original in _stored_originals(catalog)}
    names = {photo_id: original.name.lower() for photo_id, original in originals.items()}
    captures = {photo_id: capture_time(original) for photo_id, original in originals.items()}
    return SortKeys(names, captures)


def capture_time(original: Path) -> float | None:
    if not original.is_file():
        return None
    stamp = _exif_capture(original)
    return stamp if stamp is not None else original.stat().st_mtime


def sort_indexes(
    indexes: list[Path], mode: str, keys: SortKeys, markers: dict[Path, dict[str, str]]
) -> list[Path]:
    if mode not in SORT_MODES:
        raise ValueError(f"Unknown sort mode: {mode}")
    return sorted(indexes, key=IndexOrder(mode, keys, markers).key)


class IndexOrder:
    def __init__(self, mode: str, keys: SortKeys, markers: dict[Path, dict[str, str]]) -> None:
        self._mode = mode
        self._keys = keys
        self._markers = markers

    def key(self, path: Path) -> tuple:
        photo_id = _id(path)
        if self._mode == NAME:
            return self._keys.names.get(photo_id, ""), photo_id
        if self._mode == CAPTURE:
            return _capture_key(self._keys.captures.get(photo_id), photo_id)
        if self._mode == RATING:
            return -_rating(self._markers.get(path, {})), photo_id
        return (photo_id,)


def _capture_key(stamp: float | None, photo_id: int) -> tuple[bool, float, int]:
    return stamp is None, stamp or 0.0, photo_id


def _id(path: Path) -> int:
    return photo_id_of_index(path) or 0


def _rating(marks: dict[str, str]) -> int:
    try:
        return int(marks.get("rating", "0"))
    except ValueError:
        return 0


def _exif_capture(original: Path) -> float | None:
    try:
        with original.open("rb") as handle:
            tags = exifread.process_file(handle, details=False, stop_tag="DateTimeOriginal")
    except OSError:
        return None
    return _parse_stamp(str(tags.get(CAPTURE_TAG, "")))


def _parse_stamp(text: str) -> float | None:
    try:
        return datetime.strptime(text.strip(), CAPTURE_FORMAT).timestamp()
    except ValueError:
        return None


def _stored_originals(catalog: Path) -> list[tuple[int, Path]]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        rows = connection.execute(ORIGINALS).fetchall()
    finally:
        connection.close()
    return [(int(row[0]), Path(str(row[1]))) for row in rows]
