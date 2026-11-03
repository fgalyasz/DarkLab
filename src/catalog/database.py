from __future__ import annotations

import sqlite3
from pathlib import Path

from src.catalog.integrity import require_healthy
from src.catalog.locations import database_file, prepare_package
from src.catalog.migrations import migrate_catalog
from src.catalog.schema_sql import (
    ADD_COLOR, ADD_HASH, ADD_PICK, ADD_RATING, ADD_SETTINGS, FOLDERS_TABLE, META_ROW, META_TABLE,
    PHOTO_TABLE, SCHEMA_QUERY,
)

PATH_QUERY = "SELECT original_path FROM photos ORDER BY id"


def with_catalog_suffix(path: Path) -> Path:
    if path.suffix == ".darklab":
        return path
    return path.with_suffix(".darklab")


def create_catalog(path: Path) -> Path:
    destination = with_catalog_suffix(path)
    if destination.is_file():
        return open_catalog(destination)
    prepare_package(destination)
    apply_schema(database_file(destination))
    return destination


def apply_schema(path: Path) -> None:
    connection = sqlite3.connect(path)
    try:
        _create_tables(connection)
        _ensure_column(connection, ADD_HASH)
        _ensure_column(connection, ADD_SETTINGS)
        _ensure_marks(connection)
    finally:
        connection.close()


def _ensure_marks(connection: sqlite3.Connection) -> None:
    for statement in (ADD_RATING, ADD_PICK, ADD_COLOR):
        _ensure_column(connection, statement)


def _create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(META_TABLE)
    connection.execute(META_ROW)
    connection.execute(PHOTO_TABLE)
    connection.execute(FOLDERS_TABLE)
    connection.commit()


def _ensure_column(connection: sqlite3.Connection, statement: str) -> None:
    try:
        connection.execute(statement)
        connection.commit()
    except sqlite3.OperationalError as error:
        connection.rollback()
        _ignore_duplicate_column(error)


def _ignore_duplicate_column(error: sqlite3.OperationalError) -> None:
    if "duplicate column" not in str(error):
        raise error


def open_catalog(path: Path) -> Path:
    _require_existing(path)
    require_healthy(path)
    stored = read_schema(path)
    if stored is None:
        raise ValueError(f"Not a DarkLab catalog: {path}")
    migrate_catalog(path, stored)
    apply_schema(database_file(path))
    return path


def _require_existing(path: Path) -> None:
    if not database_file(path).is_file():
        raise FileNotFoundError(path)


def read_schema(path: Path) -> str | None:
    database = database_file(path)
    if not database.is_file():
        raise FileNotFoundError(path)
    return _schema_row(database)


def _schema_row(path: Path) -> str | None:
    try:
        return _fetch_schema(path)
    except sqlite3.OperationalError:
        return None


def _fetch_schema(path: Path) -> str | None:
    connection = sqlite3.connect(path)
    try:
        row = connection.execute(SCHEMA_QUERY).fetchone()
    finally:
        connection.close()
    if row is None:
        return None
    return str(row[0])


def original_paths(path: Path) -> list[str]:
    connection = sqlite3.connect(database_file(path))
    try:
        rows = connection.execute(PATH_QUERY).fetchall()
    finally:
        connection.close()
    return [str(row[0]) for row in rows]
