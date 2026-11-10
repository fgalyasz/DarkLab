from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.catalog.database import create_catalog
from src.catalog.develop_settings import write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.locations import (
    DATABASE_NAME,
    PREVIEWS_NAME,
    SETTINGS_NAME,
    package_root,
)
from src.catalog.marks import read_photo_marks, write_mark
from src.develop.tone_settings import encode_tone
from src.exporting.batch import export_photos
from src.exporting.preset import BUILT_IN_PRESET
from src.importing.originals import import_originals

SMOKE_COLORS = ((10, 20, 30), (40, 50, 60), (70, 80, 90), (100, 110, 120))


def assert_adr2_catalog_layout(catalog: Path) -> None:
    root = package_root(catalog)
    if not root.is_dir():
        raise AssertionError(f"Catalog root must be a folder: {root}")
    for name in (DATABASE_NAME, SETTINGS_NAME):
        path = root / name
        if not path.is_file():
            raise AssertionError(f"Missing catalog file: {path}")
    previews = root / PREVIEWS_NAME
    if not previews.is_dir():
        raise AssertionError(f"Missing previews directory: {previews}")


def _fixture_originals(card: Path) -> list[Path]:
    paths: list[Path] = []
    for index, color in enumerate(SMOKE_COLORS):
        path = card / f"IMG_{index}.jpg"
        Image.new("RGB", (12, 10), color).save(path, format="JPEG")
        paths.append(path)
    return paths


def _import_and_flag(catalog: Path, originals: list[Path]) -> None:
    imported = import_originals(catalog, originals)
    if imported != len(originals):
        raise AssertionError(f"Expected {len(originals)} imports, got {imported}")
    write_mark(catalog, 1, "pick", "accepted")
    if read_photo_marks(catalog, 1)["pick"] != "accepted":
        raise AssertionError("Flag did not persist on photo 1")


def _develop_and_export(catalog: Path, work_root: Path) -> None:
    write_develop_settings(catalog, 1, encode_tone({"Exposure": 3}))
    export_dir = work_root / "client"
    export_dir.mkdir(parents=True, exist_ok=True)
    report = export_photos(catalog, [1, 2, 3, 4], export_dir, BUILT_IN_PRESET)
    if len(report.written) != 4:
        raise AssertionError(f"Expected 4 exports, got {len(report.written)}")


def _assert_originals_unchanged(originals: list[Path], before: dict[Path, str]) -> None:
    after = {path: content_hash(path) for path in originals}
    if after != before:
        raise AssertionError("Original file hashes changed during smoke path")


def run_milestone_one_shoot(work_root: Path) -> Path:
    catalog = create_catalog(work_root / "shoot")
    card = work_root / "card"
    card.mkdir(parents=True, exist_ok=True)
    originals = _fixture_originals(card)
    before = {path: content_hash(path) for path in originals}
    _import_and_flag(catalog, originals)
    _develop_and_export(catalog, work_root)
    _assert_originals_unchanged(originals, before)
    assert_adr2_catalog_layout(catalog)
    return catalog
