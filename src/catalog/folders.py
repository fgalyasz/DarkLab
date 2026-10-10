from __future__ import annotations

import sqlite3
from pathlib import Path

from src.catalog.locations import database_file

INSERT_FOLDER = "INSERT OR IGNORE INTO folders (folder_path) VALUES (?)"
FOLDER_QUERY = "SELECT folder_path FROM folders ORDER BY id"


def add_imported_folder(catalog: Path, folder: Path) -> None:
    text = str(folder).strip()
    if text == "":
        raise ValueError("Folder path is empty")
    _store_folder(database_file(catalog), text)


def imported_folders(catalog: Path) -> list[str]:
    return _folder_rows(database_file(catalog))


def _store_folder(database: Path, folder: str) -> None:
    connection = sqlite3.connect(database)
    try:
        connection.execute(INSERT_FOLDER, (folder,))
        connection.commit()
    finally:
        connection.close()


def _folder_rows(database: Path) -> list[str]:
    connection = sqlite3.connect(database)
    try:
        rows = connection.execute(FOLDER_QUERY).fetchall()
    finally:
        connection.close()
    return [str(row[0]) for row in rows]
