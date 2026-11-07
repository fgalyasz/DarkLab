from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.catalog.catalog_settings import read_catalog_settings, write_catalog_setting

STANDARD_EDGE_KEY = "preview.standard_long_edge"
STANDARD_QUALITY_KEY = "preview.standard_quality"
FULL_EDGE_KEY = "preview.full_long_edge"
FULL_QUALITY_KEY = "preview.full_quality"
DISCARD_ENABLED_KEY = "preview.discard_full_enabled"
DISCARD_DAYS_KEY = "preview.discard_full_days"

DEFAULT_STANDARD_EDGE = 360
DEFAULT_STANDARD_QUALITY = 80
DEFAULT_FULL_EDGE = 2048
DEFAULT_FULL_QUALITY = 85
DEFAULT_DISCARD_DAYS = 7

MIN_EDGE = 64
MAX_EDGE = 16384
MIN_QUALITY = 50
MAX_QUALITY = 100
MIN_DISCARD_DAYS = 1
MAX_DISCARD_DAYS = 365


@dataclass(frozen=True)
class PreviewPolicy:
    standard_long_edge: int
    standard_quality: int
    full_long_edge: int
    full_quality: int
    discard_full_enabled: bool
    discard_full_days: int


def read_preview_policy(catalog: Path) -> PreviewPolicy:
    settings = read_catalog_settings(catalog)
    return PreviewPolicy(
        _edge(settings.get(STANDARD_EDGE_KEY), DEFAULT_STANDARD_EDGE),
        _quality(settings.get(STANDARD_QUALITY_KEY), DEFAULT_STANDARD_QUALITY),
        _edge(settings.get(FULL_EDGE_KEY), DEFAULT_FULL_EDGE),
        _quality(settings.get(FULL_QUALITY_KEY), DEFAULT_FULL_QUALITY),
        _enabled(settings.get(DISCARD_ENABLED_KEY)),
        _discard_days(settings.get(DISCARD_DAYS_KEY)),
    )


def store_preview_policy(catalog: Path, policy: PreviewPolicy) -> None:
    write_catalog_setting(catalog, STANDARD_EDGE_KEY, str(policy.standard_long_edge))
    write_catalog_setting(catalog, STANDARD_QUALITY_KEY, str(policy.standard_quality))
    write_catalog_setting(catalog, FULL_EDGE_KEY, str(policy.full_long_edge))
    write_catalog_setting(catalog, FULL_QUALITY_KEY, str(policy.full_quality))
    write_catalog_setting(
        catalog, DISCARD_ENABLED_KEY, "true" if policy.discard_full_enabled else "false",
    )
    write_catalog_setting(catalog, DISCARD_DAYS_KEY, str(policy.discard_full_days))


def _edge(raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    return _clamp(int(raw), MIN_EDGE, MAX_EDGE)


def _quality(raw: str | None, default: int) -> int:
    if raw is None or raw.strip() == "":
        return default
    return _clamp(int(raw), MIN_QUALITY, MAX_QUALITY)


def _enabled(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _discard_days(raw: str | None) -> int:
    if raw is None or raw.strip() == "":
        return DEFAULT_DISCARD_DAYS
    return _clamp(int(raw), MIN_DISCARD_DAYS, MAX_DISCARD_DAYS)


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(high, value))
