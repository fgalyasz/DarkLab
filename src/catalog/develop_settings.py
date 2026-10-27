from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from src.catalog.locations import database_file

READ_SETTINGS = "SELECT develop_settings FROM photos WHERE id = ?"
WRITE_SETTINGS = "UPDATE photos SET develop_settings = ? WHERE id = ?"


def read_develop_settings(catalog: Path, photo_id: int) -> dict[str, str]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        row = connection.execute(READ_SETTINGS, (photo_id,)).fetchone()
    finally:
        connection.close()
    return _decoded(row)


def write_develop_settings(catalog: Path, photo_id: int, settings: dict[str, str]) -> None:
    connection = sqlite3.connect(database_file(catalog))
    try:
        connection.execute(WRITE_SETTINGS, (json.dumps(settings, sort_keys=True), photo_id))
        connection.commit()
    finally:
        connection.close()


def _decoded(row: tuple[object, ...] | None) -> dict[str, str]:
    if row is None or row[0] is None:
        return {}
    return {str(key): str(value) for key, value in json.loads(str(row[0])).items()}
