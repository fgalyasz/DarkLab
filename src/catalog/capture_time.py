from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import exifread

from src.catalog.database import apply_schema
from src.catalog.locations import database_file

logger = logging.getLogger(__name__)

CAPTURE_TAG = "EXIF DateTimeOriginal"
CAPTURE_FORMAT = "%Y:%m:%d %H:%M:%S"
UNDATED_ORIGINALS = "SELECT id, original_path FROM photos WHERE capture_time IS NULL ORDER BY id"
WRITE_CAPTURE = "UPDATE photos SET capture_time = ? WHERE id = ?"


def capture_time(original: Path) -> float | None:
    if not original.is_file():
        return None
    stamp = _exif_capture(original)
    return stamp if stamp is not None else original.stat().st_mtime


def fill_missing_capture_times(catalog: Path) -> int:
    database = database_file(catalog)
    apply_schema(database)
    connection = sqlite3.connect(database)
    try:
        filled = _fill_undated(connection)
        connection.commit()
    finally:
        connection.close()
    logger.debug("Stored %s capture time(s) for %s", filled, catalog)
    return filled


def _fill_undated(connection: sqlite3.Connection) -> int:
    found = [(capture_time(Path(str(path))), int(photo_id)) for photo_id, path in _undated(connection)]
    dated = [(stamp, photo_id) for stamp, photo_id in found if stamp is not None]
    connection.executemany(WRITE_CAPTURE, dated)
    return len(dated)


def _undated(connection: sqlite3.Connection) -> list[tuple[object, object]]:
    return connection.execute(UNDATED_ORIGINALS).fetchall()


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
