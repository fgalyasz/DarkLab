from __future__ import annotations

import sqlite3
from pathlib import Path

from src.catalog.database import apply_schema
from src.catalog.locations import database_file

RATINGS = ("0", "1", "2", "3", "4", "5")
PICKS = ("none", "accepted", "rejected")
COLORS = ("none", "red", "orange", "yellow", "green", "blue", "purple")
ALLOWED = {"rating": RATINGS, "pick": PICKS, "color": COLORS}
DEFAULTS = {"rating": "0", "pick": "none", "color": "none"}
READ_ALL = "SELECT id, rating, pick, color FROM photos"
READ_ONE = "SELECT id, rating, pick, color FROM photos WHERE id = ?"
WRITE_COLUMN = "UPDATE photos SET {column} = ? WHERE id = ?"


def write_mark(catalog: Path, photo_id: int, kind: str, value: str) -> None:
    _require_allowed(kind, value)
    connection = _connect(catalog)
    try:
        connection.execute(WRITE_COLUMN.format(column=kind), (value, photo_id))
        connection.commit()
    finally:
        connection.close()


def read_marks(catalog: Path) -> dict[int, dict[str, str]]:
    return {int(row[0]): _marks_of(row) for row in _rows(catalog, READ_ALL, ())}


def read_photo_marks(catalog: Path, photo_id: int) -> dict[str, str]:
    rows = _rows(catalog, READ_ONE, (photo_id,))
    if not rows:
        return dict(DEFAULTS)
    return _marks_of(rows[0])


def _require_allowed(kind: str, value: str) -> None:
    if kind not in ALLOWED:
        raise ValueError(f"Unknown mark: {kind}")
    if value not in ALLOWED[kind]:
        raise ValueError(f"Mark {kind} cannot be {value!r}")


def _connect(catalog: Path) -> sqlite3.Connection:
    database = database_file(catalog)
    apply_schema(database)
    return sqlite3.connect(database)


def _rows(catalog: Path, query: str, parameters: tuple[int, ...]) -> list[tuple[object, ...]]:
    connection = _connect(catalog)
    try:
        return connection.execute(query, parameters).fetchall()
    finally:
        connection.close()


def _marks_of(row: tuple[object, ...]) -> dict[str, str]:
    values = (row[1], row[2], row[3])
    return {kind: _text_or_default(kind, value) for kind, value in zip(DEFAULTS, values)}


def _text_or_default(kind: str, value: object) -> str:
    if value is None:
        return DEFAULTS[kind]
    return str(value)
