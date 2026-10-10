import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.catalog.database import create_catalog, original_paths
from src.catalog.index_images import list_index_images, write_index_image
from src.catalog.locations import database_file
from src.catalog.removal import photo_id_of_index, remove_catalog_photo, remove_indexes


class CatalogRemovalTests(unittest.TestCase):
    def test_index_only_keeps_the_original_file(self) -> None:
        catalog, original = _catalog_with_photo()
        remove_catalog_photo(catalog, 1, delete_original=False)
        self.assertTrue(original.is_file())
        self.assertEqual(list_index_images(catalog), [])
        self.assertEqual(original_paths(catalog), [])

    def test_original_can_be_deleted_from_disk(self) -> None:
        catalog, original = _catalog_with_photo()
        remove_catalog_photo(catalog, 1, delete_original=True)
        self.assertFalse(original.is_file())
        self.assertEqual(list_index_images(catalog), [])
        self.assertEqual(original_paths(catalog), [])

    def test_a_missing_original_still_leaves_the_catalog(self) -> None:
        catalog, original = _catalog_with_photo()
        original.unlink()
        remove_catalog_photo(catalog, 1, delete_original=True)
        self.assertEqual(list_index_images(catalog), [])
        self.assertEqual(original_paths(catalog), [])

    def test_a_failed_delete_keeps_the_photo(self) -> None:
        catalog, original = _catalog_with_photo()
        with patch("src.catalog.removal._unlink_file", side_effect=OSError("busy")):
            self.assertEqual(remove_indexes(catalog, [1], True), 0)
        self.assertTrue(original.is_file())
        self.assertEqual(len(list_index_images(catalog)), 1)
        self.assertEqual(original_paths(catalog), [str(original)])

    def test_another_photo_stays(self) -> None:
        catalog, original = _catalog_with_photo()
        second = original.parent / "b.jpg"
        second.write_bytes(b"other")
        _insert_photo(catalog, second)
        write_index_image(catalog, 2, b"index-2")
        remove_indexes(catalog, [1], False)
        self.assertEqual(original_paths(catalog), [str(second)])
        self.assertEqual([path.stem for path in list_index_images(catalog)], ["2"])

    def test_an_unknown_id_changes_nothing(self) -> None:
        catalog, original = _catalog_with_photo()
        remove_catalog_photo(catalog, 9, delete_original=True)
        self.assertTrue(original.is_file())
        self.assertEqual(len(list_index_images(catalog)), 1)

    def test_photo_id_comes_from_the_index_name(self) -> None:
        self.assertEqual(photo_id_of_index(Path("previews/4.jpg")), 4)
        self.assertIsNone(photo_id_of_index(Path("notes.txt")))
        self.assertIsNone(photo_id_of_index(Path("0.jpg")))


def _catalog_with_photo() -> tuple[Path, Path]:
    root = Path(tempfile.mkdtemp())
    catalog = create_catalog(root / "wedding")
    original = root / "a.jpg"
    original.write_bytes(b"raw-bytes")
    _insert_photo(catalog, original)
    write_index_image(catalog, 1, b"index")
    return catalog, original


def _insert_photo(catalog: Path, original: Path) -> None:
    connection = sqlite3.connect(database_file(catalog))
    try:
        connection.execute(
            "INSERT INTO photos (original_path, content_hash) VALUES (?, ?)",
            (str(original), "abc"),
        )
        connection.commit()
    finally:
        connection.close()
