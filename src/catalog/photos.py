from __future__ import annotations

import sqlite3
from pathlib import Path

from src.catalog.file_hash import content_hash
from src.catalog.locations import database_file

FIND_PHOTO = "SELECT id FROM photos WHERE original_path = ?"
FIND_HASH = "SELECT id FROM photos WHERE content_hash = ? ORDER BY id LIMIT 1"
INSERT_PHOTO = "INSERT INTO photos (original_path, content_hash) VALUES (?, ?)"
MISSING_HASH = "SELECT id, original_path FROM photos WHERE content_hash IS NULL"
WRITE_HASH = "UPDATE photos SET content_hash = ? WHERE id = ? AND content_hash IS NULL"
READ_HASH = "SELECT content_hash FROM photos WHERE original_path = ?"


def known_content(catalog: Path, digest: str) -> bool:
    return _hash_id(database_file(catalog), digest) is not None


def add_photo(catalog: Path, original: Path, digest: str, allow_duplicate: bool) -> int | None:
    database = database_file(catalog)
    if _existing_photo(database, str(original)) is not None:
        return None
    if _blocked_hash(database, digest, allow_duplicate):
        return None
    return _insert_photo(database, str(original), digest)


def _existing_photo(database: Path, original: str) -> int | None:
    connection = sqlite3.connect(database)
    try:
        row = connection.execute(FIND_PHOTO, (original,)).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return int(row[0])


def stored_hash(catalog: Path, original: Path) -> str | None:
    connection = sqlite3.connect(database_file(catalog))
    try:
        row = connection.execute(READ_HASH, (str(original),)).fetchone()
    finally:
        connection.close()
    if row is None or row[0] is None:
        return None
    return str(row[0])


def fill_missing_hashes(catalog: Path) -> None:
    for photo_id, raw in _rows_without_hash(database_file(catalog)):
        _fill_one(catalog, photo_id, Path(raw))


def _blocked_hash(database: Path, digest: str, allow_duplicate: bool) -> bool:
    if allow_duplicate:
        return False
    return _hash_id(database, digest) is not None


def _hash_id(database: Path, digest: str) -> int | None:
    connection = sqlite3.connect(database)
    try:
        row = connection.execute(FIND_HASH, (digest,)).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return int(row[0])


def _insert_photo(database: Path, original: str, digest: str) -> int:
    connection = sqlite3.connect(database)
    try:
        cursor = connection.execute(INSERT_PHOTO, (original, digest))
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()


def _rows_without_hash(database: Path) -> list[tuple[int, str]]:
    connection = sqlite3.connect(database)
    try:
        rows = connection.execute(MISSING_HASH).fetchall()
    finally:
        connection.close()
    return [(int(row[0]), str(row[1])) for row in rows]


def _fill_one(catalog: Path, photo_id: int, path: Path) -> None:
    if not path.is_file():
        return
    _write_hash(database_file(catalog), photo_id, content_hash(path))


def _write_hash(database: Path, photo_id: int, digest: str) -> None:
    connection = sqlite3.connect(database)
    try:
        connection.execute(WRITE_HASH, (digest, photo_id))
        connection.commit()
    finally:
        connection.close()
