import sqlite3
import tempfile
import unittest
from pathlib import Path

from src.catalog.database import (
    create_catalog, open_catalog, original_paths, read_schema,
)
from src.catalog.session import catalog_to_reopen, remember_catalog


def execute_statement(path: Path, statement: str) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute(statement)
        connection.commit()
    finally:
        connection.close()


def insert_original(path: Path, original: str) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("INSERT INTO photos (original_path) VALUES (?)", (original,))
        connection.commit()
    finally:
        connection.close()


class CatalogTests(unittest.TestCase):
    def test_create_adds_suffix_and_schema(self) -> None:
        folder = Path(tempfile.mkdtemp())
        created = create_catalog(folder / "nested" / "wedding")
        self.assertEqual(created.name, "wedding.darklab")
        self.assertEqual(open_catalog(created), created)
        self.assertEqual(read_schema(created), "1")

    def test_create_keeps_existing_suffix(self) -> None:
        folder = Path(tempfile.mkdtemp())
        created = create_catalog(folder / "named.darklab")
        self.assertEqual(created.name, "named.darklab")

    def test_create_again_keeps_photos(self) -> None:
        folder = Path(tempfile.mkdtemp())
        created = create_catalog(folder / "shoot")
        insert_original(created, "a.jpg")
        self.assertEqual(create_catalog(created), created)
        self.assertEqual(original_paths(created), ["a.jpg"])

    def test_open_missing_catalog(self) -> None:
        folder = Path(tempfile.mkdtemp())
        with self.assertRaises(FileNotFoundError):
            open_catalog(folder / "missing.darklab")

    def test_open_rejects_other_database(self) -> None:
        folder = Path(tempfile.mkdtemp())
        path = folder / "notes.darklab"
        execute_statement(path, "CREATE TABLE notes (id INTEGER)")
        with self.assertRaises(ValueError):
            open_catalog(path)

    def test_open_rejects_empty_meta(self) -> None:
        folder = Path(tempfile.mkdtemp())
        path = folder / "empty.darklab"
        statement = "CREATE TABLE catalog_meta (key TEXT PRIMARY KEY, value TEXT)"
        execute_statement(path, statement)
        with self.assertRaises(ValueError):
            open_catalog(path)

    def test_switch_does_not_merge(self) -> None:
        folder = Path(tempfile.mkdtemp())
        first = create_catalog(folder / "first")
        second = create_catalog(folder / "second")
        insert_original(first, "a.jpg")
        settings = remember_catalog({}, first)
        settings = remember_catalog(settings, second)
        self.assertEqual(catalog_to_reopen(settings), second)
        self.assertEqual(original_paths(second), [])
        self.assertEqual(original_paths(first), ["a.jpg"])

    def test_reopen_saved_catalog(self) -> None:
        folder = Path(tempfile.mkdtemp())
        created = create_catalog(folder / "wedding")
        settings = remember_catalog({}, created)
        self.assertEqual(catalog_to_reopen(settings), created)

    def test_missing_file_is_not_reopened(self) -> None:
        missing = Path(tempfile.mkdtemp()) / "gone.darklab"
        self.assertIsNone(catalog_to_reopen(remember_catalog({}, missing)))
        self.assertIsNone(catalog_to_reopen({}))
