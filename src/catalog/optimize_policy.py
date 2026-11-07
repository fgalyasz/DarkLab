from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.catalog.catalog_settings import read_catalog_settings, write_catalog_setting

ON_QUIT_KEY = "optimize.on_quit_enabled"
ON_IDLE_KEY = "optimize.on_idle_minutes"

DEFAULT_IDLE_MINUTES = 0


@dataclass(frozen=True)
class OptimizePolicy:
    on_quit_enabled: bool
    on_idle_minutes: int


def read_optimize_policy(catalog: Path) -> OptimizePolicy:
    settings = read_catalog_settings(catalog)
    return OptimizePolicy(_enabled(settings.get(ON_QUIT_KEY)), _idle(settings.get(ON_IDLE_KEY)))


def store_optimize_policy(catalog: Path, policy: OptimizePolicy) -> None:
    write_catalog_setting(
        catalog, ON_QUIT_KEY, "true" if policy.on_quit_enabled else "false",
    )
    write_catalog_setting(catalog, ON_IDLE_KEY, str(policy.on_idle_minutes))


def _enabled(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _idle(raw: str | None) -> int:
    if raw is None or raw.strip() == "":
        return DEFAULT_IDLE_MINUTES
    value = int(raw)
    return max(0, min(24 * 60, value))
