from __future__ import annotations

import sqlite3
from pathlib import Path

from src.catalog.locations import database_file, prepare_package

META_TABLE = "CREATE TABLE IF NOT EXISTS catalog_meta (key TEXT PRIMARY KEY, value TEXT)"
META_ROW = "INSERT OR IGNORE INTO catalog_meta (key, value) VALUES ('schema', '2')"
PHOTO_TABLE = (
    "CREATE TABLE IF NOT EXISTS photos "
    "(id INTEGER PRIMARY KEY, original_path TEXT, content_hash TEXT)"
)
ADD_HASH = "ALTER TABLE photos ADD COLUMN content_hash TEXT"
FOLDERS_TABLE = (
    "CREATE TABLE IF NOT EXISTS folders "
    "(id INTEGER PRIMARY KEY, folder_path TEXT NOT NULL UNIQUE)"
)
SCHEMA_QUERY = "SELECT value FROM catalog_meta WHERE key = 'schema'"
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
        _ensure_hash_column(connection)
    finally:
        connection.close()


def _create_tables(connection: sqlite3.Connection) -> None:
    connection.execute(META_TABLE)
    connection.execute(META_ROW)
    connection.execute(PHOTO_TABLE)
    connection.execute(FOLDERS_TABLE)
    connection.commit()


def _ensure_hash_column(connection: sqlite3.Connection) -> None:
    try:
        connection.execute(ADD_HASH)
        connection.commit()
    except sqlite3.OperationalError as error:
        connection.rollback()
        _ignore_duplicate_column(error)


def _ignore_duplicate_column(error: sqlite3.OperationalError) -> None:
    if "duplicate column" not in str(error):
        raise error


def open_catalog(path: Path) -> Path:
    if read_schema(path) is None:
        raise ValueError(f"Not a DarkLab catalog: {path}")
    return path


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
