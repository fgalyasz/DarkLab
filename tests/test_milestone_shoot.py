import tempfile
import unittest
from pathlib import Path

from PIL import Image

from src.catalog.database import create_catalog
from src.catalog.develop_settings import write_develop_settings
from src.catalog.file_hash import content_hash
from src.develop.tone_settings import encode_tone
from src.exporting.batch import export_photos
from src.exporting.preset import BUILT_IN_PRESET
from src.importing.originals import import_originals

COLORS = ((10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120))


def _jpeg(folder: Path, name: str, color: tuple[int, int, int]) -> Path:
    path = folder / name
    Image.new("RGB", (12, 10), color).save(path, format="JPEG")
    return path


class MilestoneShootTests(unittest.TestCase):
    def test_import_develop_export_keeps_original_hashes(self) -> None:
        root = Path(tempfile.mkdtemp())
        catalog = create_catalog(root / "shoot")
        card = root / "card"
        card.mkdir()
        originals = [_jpeg(card, f"IMG_{index}.jpg", color) for index, color in enumerate(COLORS)]
        before = {path: content_hash(path) for path in originals}
        self.assertEqual(import_originals(catalog, originals), 4)
        write_develop_settings(catalog, 1, encode_tone({"Exposure": 3}))
        export_dir = root / "client"
        export_dir.mkdir()
        report = export_photos(catalog, [1, 2, 3, 4], export_dir, BUILT_IN_PRESET)
        self.assertEqual(len(report.written), 4)
        self.assertEqual({path: content_hash(path) for path in originals}, before)


if __name__ == "__main__":
    unittest.main()
