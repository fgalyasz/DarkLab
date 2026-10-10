from __future__ import annotations

import sqlite3
from pathlib import Path

from src.catalog.locations import database_file

FIND_PHOTO = "SELECT id FROM photos WHERE original_path = ?"
INSERT_PHOTO = "INSERT INTO photos (original_path) VALUES (?)"


def remember_photo(catalog: Path, original: Path) -> int:
    database = database_file(catalog)
    found = _existing_photo(database, str(original))
    if found is not None:
        return found
    return _insert_photo(database, str(original))


def _existing_photo(database: Path, original: str) -> int | None:
    connection = sqlite3.connect(database)
    try:
        row = connection.execute(FIND_PHOTO, (original,)).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return int(row[0])


def _insert_photo(database: Path, original: str) -> int:
    connection = sqlite3.connect(database)
    try:
        cursor = connection.execute(INSERT_PHOTO, (original,))
        connection.commit()
        return int(cursor.lastrowid)
    finally:
        connection.close()
