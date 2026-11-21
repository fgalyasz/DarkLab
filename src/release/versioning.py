from __future__ import annotations

import sys
from pathlib import Path


def read_version_text(raw: str) -> str:
    version = raw.strip()
    if version == "":
        raise ValueError("Version file is empty")
    parse_semver(version)
    return version


def parse_semver(version: str) -> tuple[int, int, int]:
    parts = version.split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"Invalid semver: {version}")
    return int(parts[0]), int(parts[1]), int(parts[2])


def is_newer(candidate: str, current: str) -> bool:
    return parse_semver(candidate) > parse_semver(current)


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def resolve_version_file() -> Path:
    meipass = getattr(sys, "_MEIPASS", None)
    if getattr(sys, "frozen", False) and meipass is not None:
        return Path(meipass) / "docs" / "version.txt"
    return project_root() / "docs" / "version.txt"


def app_version(path: Path | None = None) -> str:
    target = path if path is not None else resolve_version_file()
    return read_version_text(target.read_text(encoding="utf-8"))
