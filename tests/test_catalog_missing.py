import sqlite3
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.catalog.database import create_catalog
from src.catalog.develop_settings import read_develop_settings, write_develop_settings
from src.catalog.locations import database_file
from src.catalog.index_images import index_image_path
from src.catalog.missing import (
    MissingPhoto, RelinkError, is_missing, missing_index_paths, missing_photos, relink_photo,
)
from src.importing.originals import import_originals

SETTINGS = {"Exposure": "0.5"}


def _original(folder: Path, name: str, color: str) -> Path:
    path = folder / name
    Image.new("RGB", (8, 8), color).save(path)
    return path


class MissingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.catalog = create_catalog(self.folder / "shoot")
        self.original = _original(self.folder, "a.png", "red")
        import_originals(self.catalog, [self.original])
        write_develop_settings(self.catalog, 1, SETTINGS)

    def test_present_original_is_not_missing(self) -> None:
        self.assertEqual(missing_photos(self.catalog), [])
        self.assertFalse(is_missing(self.catalog, 1))

    def test_removed_original_is_listed_and_the_photo_stays(self) -> None:
        self.original.unlink()
        self.assertEqual(missing_photos(self.catalog), [MissingPhoto(1, self.original)])
        self.assertTrue(is_missing(self.catalog, 1))

    def test_missing_index_paths_name_the_index_image_of_each_missing_photo(self) -> None:
        self.assertEqual(missing_index_paths(self.catalog), set())
        self.original.unlink()
        self.assertEqual(missing_index_paths(self.catalog), {index_image_path(self.catalog, 1)})

    def test_relink_to_same_content_clears_missing_and_keeps_settings(self) -> None:
        data = self.original.read_bytes()
        self.original.unlink()
        moved = self.folder / "moved.png"
        moved.write_bytes(data)
        relink_photo(self.catalog, 1, moved)
        self.assertEqual(missing_photos(self.catalog), [])
        self.assertEqual(read_develop_settings(self.catalog, 1), SETTINGS)

    def test_relink_to_different_content_needs_confirmation(self) -> None:
        self.original.unlink()
        other = _original(self.folder, "b.png", "blue")
        with self.assertRaises(RelinkError):
            relink_photo(self.catalog, 1, other)
        self.assertTrue(is_missing(self.catalog, 1))

    def test_confirmed_relink_to_different_content_is_accepted(self) -> None:
        self.original.unlink()
        other = _original(self.folder, "b.png", "blue")
        relink_photo(self.catalog, 1, other, confirm_different=True)
        self.assertFalse(is_missing(self.catalog, 1))
        self.assertEqual(read_develop_settings(self.catalog, 1), SETTINGS)

    def test_relink_to_absent_file_is_rejected(self) -> None:
        with self.assertRaises(RelinkError):
            relink_photo(self.catalog, 1, self.folder / "nope.png")

    def test_relink_of_unknown_photo_is_rejected(self) -> None:
        with self.assertRaises(RelinkError):
            relink_photo(self.catalog, 99, self.original)

    def test_relink_of_photo_without_stored_hash_is_accepted(self) -> None:
        connection = sqlite3.connect(database_file(self.catalog))
        connection.execute("UPDATE photos SET content_hash = NULL")
        connection.commit()
        connection.close()
        relink_photo(self.catalog, 1, self.original)
        self.assertFalse(is_missing(self.catalog, 1))


if __name__ == "__main__":
    unittest.main()
