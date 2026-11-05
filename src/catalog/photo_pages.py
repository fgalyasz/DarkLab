from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from pathlib import Path

from src.catalog.index_images import index_image_path
from src.catalog.locations import database_file

logger = logging.getLogger(__name__)

PAGE_SIZE = 1000
PHOTO_ID_PAGE = "SELECT id FROM photos WHERE id > ? ORDER BY id LIMIT ?"


def list_catalog_indexes(catalog: Path, page_size: int = PAGE_SIZE) -> list[Path]:
    return [index_image_path(catalog, photo_id) for page in iter_photo_id_pages(catalog, page_size) for photo_id in page]


def iter_photo_id_pages(catalog: Path, page_size: int = PAGE_SIZE) -> Iterator[list[int]]:
    if page_size < 1:
        raise ValueError(f"Page size must be at least 1: {page_size}")
    database = database_file(catalog)
    if not database.is_file():
        return
    try:
        yield from _read_pages(database, page_size)
    except sqlite3.Error as error:
        logger.warning("Could not page photos of %s: %s", catalog, error)


def _read_pages(database: Path, page_size: int) -> Iterator[list[int]]:
    connection = sqlite3.connect(database)
    try:
        last_id = 0
        while page := _read_page(connection, last_id, page_size):
            yield page
            last_id = page[-1]
    finally:
        connection.close()


def _read_page(connection: sqlite3.Connection, last_id: int, page_size: int) -> list[int]:
    return [int(row[0]) for row in connection.execute(PHOTO_ID_PAGE, (last_id, page_size)).fetchall()]
