import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.catalog.database import create_catalog
from src.catalog.develop_settings import read_develop_settings, write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.photos import add_photo
from src.catalog.sidecar import SidecarError, read_sidecar, sidecar_path, write_sidecar
from src.importing.originals import import_originals

FOREIGN_XMP = (
    '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?><x:xmpmeta xmlns:x="adobe:ns:meta/">'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    '<rdf:Description rdf:about="" xmlns:xmp="http://ns.adobe.com/xap/1.0/" xmp:Rating="3"/>'
    "</rdf:RDF></x:xmpmeta><?xpacket end=\"w\"?>"
)
SETTINGS = {"Exposure": "0.5", "Contrast": "10"}


def _original(folder: Path, name: str = "frame.jpg") -> Path:
    path = folder / name
    Image.new("RGB", (8, 8), "gray").save(path)
    return path


class SidecarTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.original = _original(self.folder)

    def test_sidecar_sits_beside_the_original(self) -> None:
        self.assertEqual(sidecar_path(self.original), self.folder / "frame.xmp")

    def test_write_then_read_round_trips_settings(self) -> None:
        write_sidecar(self.original, SETTINGS)
        self.assertEqual(read_sidecar(self.original), SETTINGS)

    def test_write_leaves_original_hash_unchanged(self) -> None:
        before = content_hash(self.original)
        write_sidecar(self.original, SETTINGS)
        self.assertEqual(content_hash(self.original), before)

    def test_write_keeps_unrelated_tag(self) -> None:
        sidecar_path(self.original).write_text(FOREIGN_XMP, encoding="utf-8")
        write_sidecar(self.original, SETTINGS)
        self.assertIn('xmp:Rating="3"', sidecar_path(self.original).read_text(encoding="utf-8"))
        self.assertEqual(read_sidecar(self.original), SETTINGS)

    def test_write_leaves_no_staged_file(self) -> None:
        write_sidecar(self.original, SETTINGS)
        self.assertEqual(sorted(path.name for path in self.folder.glob("*.xmp")), ["frame.xmp"])

    def test_dropped_foreign_tag_fails_and_keeps_previous_sidecar(self) -> None:
        sidecar_path(self.original).write_text(FOREIGN_XMP, encoding="utf-8")
        with patch("src.catalog.sidecar._read_tags", side_effect=[{"Xmp.xmp.Rating": "3"}, {}]):
            with self.assertRaises(SidecarError):
                write_sidecar(self.original, SETTINGS)
        self.assertEqual(sidecar_path(self.original).read_text(encoding="utf-8"), FOREIGN_XMP)
        self.assertEqual(list(self.folder.glob("*.darklab-tmp.xmp")), [])

    def test_read_without_sidecar_is_empty(self) -> None:
        self.assertEqual(read_sidecar(self.original), {})

    def test_read_of_damaged_sidecar_is_empty(self) -> None:
        sidecar_path(self.original).write_text("not xmp at all", encoding="utf-8")
        with patch("src.catalog.sidecar._read_tags", side_effect=RuntimeError("bad xmp")):
            self.assertEqual(read_sidecar(self.original), {})


class DevelopSettingsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.catalog = create_catalog(self.folder / "shoot")
        self.original = _original(self.folder)

    def _photo_id(self) -> int:
        photo_id = add_photo(self.catalog, self.original, content_hash(self.original), False)
        assert photo_id is not None
        return photo_id

    def test_new_photo_has_no_settings(self) -> None:
        self.assertEqual(read_develop_settings(self.catalog, self._photo_id()), {})

    def test_settings_round_trip_through_the_catalog(self) -> None:
        photo_id = self._photo_id()
        write_develop_settings(self.catalog, photo_id, SETTINGS)
        self.assertEqual(read_develop_settings(self.catalog, photo_id), SETTINGS)

    def test_unknown_photo_has_no_settings(self) -> None:
        self.assertEqual(read_develop_settings(self.catalog, 999), {})

    def test_import_restores_settings_from_the_sidecar(self) -> None:
        write_sidecar(self.original, SETTINGS)
        self.assertEqual(import_originals(self.catalog, [self.original]), 1)
        self.assertEqual(read_develop_settings(self.catalog, 1), SETTINGS)

    def test_import_without_sidecar_leaves_settings_empty(self) -> None:
        import_originals(self.catalog, [self.original])
        self.assertEqual(read_develop_settings(self.catalog, 1), {})

    def test_second_catalog_gets_settings_from_the_same_sidecar(self) -> None:
        write_sidecar(self.original, SETTINGS)
        second = create_catalog(self.folder / "again")
        import_originals(second, [self.original])
        self.assertEqual(read_develop_settings(second, 1), SETTINGS)


if __name__ == "__main__":
    unittest.main()
