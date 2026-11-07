from __future__ import annotations

import logging
import os
import sqlite3
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path

from src.catalog.database import apply_schema
from src.catalog.locations import database_file

logger = logging.getLogger(__name__)

CAPTURE = "capture"
NAME = "name"
IMPORTED = "imported"
RATING = "rating"
SORT_MODES = (CAPTURE, NAME, IMPORTED, RATING)
ANY = "any"

RATING_VALUE = "CAST(COALESCE(rating, '0') AS INTEGER)"
SELECT_IDS = "SELECT id FROM photos{where} ORDER BY {order}"
SELECT_NAMES = "SELECT id, original_path FROM photos{where}"
ORDER_BY = {
    CAPTURE: "capture_time IS NULL, capture_time, id",
    IMPORTED: "id",
    RATING: f"-{RATING_VALUE}, id",
}


@dataclass(frozen=True)
class MarkFilter:
    minimum_rating: str = ANY
    pick: str = ANY
    color: str = ANY

    def conditions(self) -> list[tuple[str, str | int]]:
        found: list[tuple[str, str | int]] = []
        if self.minimum_rating != ANY:
            found.append((f"{RATING_VALUE} >= ?", _rating_number(self.minimum_rating)))
        if self.pick != ANY:
            found.append(("COALESCE(pick, 'none') = ?", self.pick))
        if self.color != ANY:
            found.append(("COALESCE(color, 'none') = ?", self.color))
        return found


def query_photo_ids(
    catalog: Path, marks: MarkFilter, mode: str, scope: Collection[int] | None = None
) -> list[int]:
    if mode not in SORT_MODES:
        raise ValueError(f"Unknown sort mode: {mode}")
    try:
        ordered = _ordered_ids(catalog, marks, mode)
    except sqlite3.Error as error:
        logger.warning("Could not query photos of %s: %s", catalog, error)
        return []
    return ordered if scope is None else [photo_id for photo_id in ordered if photo_id in scope]


def _ordered_ids(catalog: Path, marks: MarkFilter, mode: str) -> list[int]:
    where, parameters = _where(marks)
    if mode == NAME:
        return _name_ordered(catalog, where, parameters)
    query = SELECT_IDS.format(where=where, order=ORDER_BY[mode])
    return [int(row[0]) for row in _rows(catalog, query, parameters)]


def _name_ordered(catalog: Path, where: str, parameters: list[str | int]) -> list[int]:
    rows = _rows(catalog, SELECT_NAMES.format(where=where), parameters)
    keyed = sorted((os.path.basename(str(path)).lower(), int(photo_id)) for photo_id, path in rows)
    return [photo_id for _name, photo_id in keyed]


def _where(marks: MarkFilter) -> tuple[str, list[str | int]]:
    conditions = marks.conditions()
    if not conditions:
        return "", []
    return " WHERE " + " AND ".join(text for text, _value in conditions), [value for _text, value in conditions]


def _rating_number(minimum: str) -> int:
    try:
        return int(minimum)
    except ValueError:
        return 0


def _rows(catalog: Path, query: str, parameters: list[str | int]) -> list[tuple[object, ...]]:
    database = database_file(catalog)
    apply_schema(database)
    connection = sqlite3.connect(database)
    try:
        return connection.execute(query, parameters).fetchall()
    finally:
        connection.close()
