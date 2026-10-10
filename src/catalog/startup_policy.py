from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from src.catalog.session import catalog_to_reopen

ASK = "ask"
RECENT = "recent"
FIXED = "fixed"
MODES = (ASK, RECENT, FIXED)


def normalize_mode(value: str) -> str:
    if value in MODES:
        return value
    return RECENT


def plan_startup(settings: dict[str, str]) -> tuple[str, Path | None]:
    mode = normalize_mode(settings.get("startup_mode", ""))
    if mode == ASK:
        return ("ask", None)
    return _plan_stored(settings, mode)


def _plan_stored(settings: dict[str, str], mode: str) -> tuple[str, Path | None]:
    path = _stored_path(settings, mode)
    if path is not None:
        return ("open", path)
    return ("ask", None)


def require_catalog(settings: dict[str, str], choose: Callable[[], Path | None]) -> Path | None:
    action, path = plan_startup(settings)
    if action == "open" and path is not None:
        return path
    return choose()


def _stored_path(settings: dict[str, str], mode: str) -> Path | None:
    key = "fixed_catalog" if mode == FIXED else "catalog_path"
    return catalog_to_reopen({"catalog_path": settings.get(key, "")})


def fixed_catalog_error(path: str) -> str | None:
    if path.strip() == "":
        return "Choose a catalog."
    if _stored_path({"fixed_catalog": path.strip()}, FIXED) is None:
        return "That catalog does not exist."
    return None
