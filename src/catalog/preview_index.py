from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from src.catalog.index_images import index_image_path
from src.catalog.locations import database_file

logger = logging.getLogger(__name__)

ALL_PHOTO_IDS = "SELECT id FROM photos ORDER BY id"


def missing_preview_ids(catalog: Path) -> list[int]:
    return [
        photo_id for photo_id in _catalog_photo_ids(catalog) if not index_image_path(catalog, photo_id).is_file()
    ]


def _catalog_photo_ids(catalog: Path) -> list[int]:
    database = database_file(catalog)
    if not database.is_file():
        return []
    try:
        return _read_photo_ids(database)
    except sqlite3.Error as error:
        logger.warning("Could not list photos of %s: %s", catalog, error)
        return []


def _read_photo_ids(database: Path) -> list[int]:
    connection = sqlite3.connect(database)
    try:
        return [int(row[0]) for row in connection.execute(ALL_PHOTO_IDS).fetchall()]
    finally:
        connection.close()
