from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.catalog.database import create_catalog
from src.catalog.develop_settings import write_develop_settings
from src.catalog.file_hash import content_hash
from src.catalog.marks import write_mark
from src.develop.tone_settings import encode_tone
from src.exporting.batch import export_photos
from src.exporting.preset import BUILT_IN_PRESET
from src.importing.originals import import_originals
from src.smoke.milestone_one_shoot import assert_adr2_catalog_layout

SM1_DEFAULT_COUNT = 200


def build_fixture_card(card: Path, count: int) -> list[Path]:
    card.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for index in range(count):
        path = card / f"IMG_{index:04d}.jpg"
        tone = (index * 3 % 250, index * 5 % 250, index * 7 % 250)
        edge = 8 + (index % 5)
        Image.new("RGB", (edge, edge), tone).save(path, format="JPEG")
        paths.append(path)
    return paths


def picked_photo_ids(count: int) -> list[int]:
    return [photo_id for photo_id in range(1, count + 1) if photo_id % 5 == 1]


def _cull_picks(catalog: Path, photo_ids: list[int]) -> None:
    for photo_id in photo_ids:
        write_mark(catalog, photo_id, "pick", "accepted")


def _develop_picks(catalog: Path, photo_ids: list[int]) -> None:
    tone = encode_tone({"Exposure": 0.25})
    for photo_id in photo_ids:
        write_develop_settings(catalog, photo_id, tone)


def _export_picks(catalog: Path, work_root: Path, photo_ids: list[int]) -> None:
    export_dir = work_root / "client"
    export_dir.mkdir(parents=True, exist_ok=True)
    report = export_photos(catalog, photo_ids, export_dir, BUILT_IN_PRESET)
    if len(report.written) != len(photo_ids):
        raise AssertionError(
            f"Expected {len(photo_ids)} exports, got {len(report.written)}"
        )


def _assert_originals_unchanged(originals: list[Path], before: dict[Path, str]) -> None:
    after = {path: content_hash(path) for path in originals}
    if after != before:
        raise AssertionError("Original file hashes changed during SM-1 fixture path")


def run_sm1_fixture_shoot(work_root: Path, count: int = SM1_DEFAULT_COUNT) -> Path:
    catalog = create_catalog(work_root / "shoot")
    card = work_root / "card"
    originals = build_fixture_card(card, count)
    before = {path: content_hash(path) for path in originals}
    imported = import_originals(catalog, originals)
    if imported != count:
        raise AssertionError(f"Expected {count} imports, got {imported}")
    picks = picked_photo_ids(count)
    _cull_picks(catalog, picks)
    _develop_picks(catalog, picks)
    _export_picks(catalog, work_root, picks)
    _assert_originals_unchanged(originals, before)
    assert_adr2_catalog_layout(catalog)
    return catalog
