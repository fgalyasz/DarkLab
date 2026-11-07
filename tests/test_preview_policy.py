import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.catalog.database import create_catalog
from src.catalog.full_previews import (
    discard_stale_full_previews, full_preview_path, write_full_preview,
)
from src.catalog.index_images import index_image_path, read_index_image
from src.catalog.preview_policy import (
    DEFAULT_STANDARD_EDGE,
    PreviewPolicy,
    read_preview_policy,
    store_preview_policy,
)
from src.importing.originals import import_original, index_jpeg
from src.importing.preview_encoding import encode_full_jpeg, encode_standard_jpeg


def _photo(folder: Path) -> Path:
    path = folder / "frame.jpg"
    Image.new("RGB", (800, 600), (90, 40, 10)).save(path)
    return path


class PreviewPolicyTests(unittest.TestCase):
    def test_defaults_without_settings(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        policy = read_preview_policy(catalog)
        self.assertEqual(policy.standard_long_edge, DEFAULT_STANDARD_EDGE)
        self.assertFalse(policy.discard_full_enabled)

    def test_store_round_trips(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        wanted = PreviewPolicy(400, 85, 1024, 90, True, 14)
        store_preview_policy(catalog, wanted)
        self.assertEqual(read_preview_policy(catalog), wanted)


class PreviewEncodingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.original = _photo(Path(tempfile.mkdtemp()))

    def test_standard_respects_edge_cap(self) -> None:
        payload = encode_standard_jpeg(self.original, 120, 80)
        image = Image.open(__import__("io").BytesIO(payload))
        self.assertLessEqual(max(image.size), 120)

    def test_import_uses_catalog_policy(self) -> None:
        catalog = create_catalog(self.original.parent / "shoot")
        store_preview_policy(catalog, PreviewPolicy(100, 80, 2048, 85, False, 7))
        import_original(catalog, self.original)
        payload = read_index_image(catalog, 1)
        assert payload is not None
        image = Image.open(__import__("io").BytesIO(payload))
        self.assertLessEqual(max(image.size), 100)

    def test_full_encoding_respects_edge(self) -> None:
        payload = encode_full_jpeg(self.original, 200, 85)
        image = Image.open(__import__("io").BytesIO(payload))
        self.assertLessEqual(max(image.size), 200)

    def test_index_jpeg_without_policy_uses_legacy_default(self) -> None:
        payload = index_jpeg(self.original)
        image = Image.open(__import__("io").BytesIO(payload))
        self.assertLessEqual(max(image.size), DEFAULT_STANDARD_EDGE)


class FullPreviewDiscardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = create_catalog(Path(tempfile.mkdtemp()) / "demo")
        self.grid = index_image_path(self.catalog, 1)
        self.grid.parent.mkdir(parents=True, exist_ok=True)
        self.grid.write_bytes(b"grid")

    def test_discard_removes_only_old_full_files(self) -> None:
        full = write_full_preview(self.catalog, 1, "abc", b"full")
        policy = PreviewPolicy(360, 80, 2048, 85, True, 7)
        import os
        old = os.path.getmtime(full) - 8 * 86_400
        os.utime(full, (old, old))
        removed = discard_stale_full_previews(self.catalog, policy)
        self.assertEqual(removed, 1)
        self.assertTrue(self.grid.is_file())
        self.assertFalse(full.is_file())

    def test_discard_skipped_when_disabled(self) -> None:
        path = full_preview_path(self.catalog, 2, "x")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"x")
        policy = PreviewPolicy(360, 80, 2048, 85, False, 7)
        self.assertEqual(discard_stale_full_previews(self.catalog, policy), 0)
        self.assertTrue(path.is_file())


if __name__ == "__main__":
    unittest.main()
