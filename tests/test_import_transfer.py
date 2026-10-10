import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.importing.discover import discover_images
from src.importing.transfer import _remove_source_after_copy, copy_original, move_original


def sample(folder: Path, name: str, content: bytes) -> Path:
    path = folder / name
    path.write_bytes(content)
    return path


class TransferTests(unittest.TestCase):
    def test_copy_leaves_the_source(self) -> None:
        root = Path(tempfile.mkdtemp())
        source = sample(root, "a.jpg", b"jpeg")
        copied = copy_original(source, root / "out" / "a.jpg")
        self.assertEqual(copied.read_bytes(), b"jpeg")
        self.assertTrue(source.is_file())

    def test_move_removes_the_source_when_sizes_match(self) -> None:
        root = Path(tempfile.mkdtemp())
        source = sample(root, "a.jpg", b"jpeg")
        moved = move_original(source, root / "out" / "a.jpg")
        self.assertEqual(moved.read_bytes(), b"jpeg")
        self.assertFalse(source.exists())

    def test_failed_copy_leaves_the_source(self) -> None:
        root = Path(tempfile.mkdtemp())
        source = sample(root, "a.jpg", b"jpeg")
        blocker = sample(root, "blocked", b"x")
        with self.assertRaises(OSError):
            move_original(source, blocker / "a.jpg")
        self.assertTrue(source.is_file())

    def test_missing_destination_keeps_the_source(self) -> None:
        root = Path(tempfile.mkdtemp())
        source = sample(root, "a.jpg", b"jpeg")
        _remove_source_after_copy(source, root / "missing.jpg")
        self.assertTrue(source.is_file())

    def test_size_mismatch_keeps_the_source(self) -> None:
        root = Path(tempfile.mkdtemp())
        source = sample(root, "a.jpg", b"jpeg")
        destination = sample(root, "short.jpg", b"no")
        _remove_source_after_copy(source, destination)
        self.assertTrue(source.is_file())


class DiscoverTests(unittest.TestCase):
    def test_discover_lists_images_and_skips_other_files(self) -> None:
        root = Path(tempfile.mkdtemp())
        jpeg = sample(root, "b.jpg", b"b")
        sample(root, "notes.txt", b"x")
        nested = root / "card"
        nested.mkdir()
        raw = sample(nested, "a.ARW", b"raw")
        deep = root / "card" / "a" / "b"
        deep.mkdir(parents=True)
        sample(deep, "deep.jpg", b"d")
        self.assertEqual(discover_images(root), [jpeg])
        self.assertEqual(discover_images(root, recursive=True), [raw, jpeg])

    def test_missing_folder_is_empty(self) -> None:
        self.assertEqual(discover_images(Path(tempfile.mkdtemp()) / "gone"), [])

    def test_unreadable_folder_is_empty(self) -> None:
        folder = Path(tempfile.mkdtemp())
        with patch.object(Path, "iterdir", side_effect=OSError):
            self.assertEqual(discover_images(folder), [])
