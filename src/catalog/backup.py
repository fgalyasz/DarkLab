from __future__ import annotations

import logging
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from src.catalog.locations import (
    DATABASE_NAME, PREVIEWS_NAME, SETTINGS_NAME, database_file, package_root,
)

logger = logging.getLogger(__name__)

STAMP_FORMAT = "%Y%m%d-%H%M%S"


class BackupError(OSError):
    pass


def default_backup_root(catalog: Path) -> Path:
    root = package_root(catalog)
    return root.with_name(f"{root.name}.backups")


def backup_catalog(catalog: Path, destination_root: Path, moment: datetime | None = None) -> Path:
    stamp = (moment or datetime.now()).strftime(STAMP_FORMAT)
    target = destination_root / f"{package_root(catalog).stem}-{stamp}.darklab"
    _require_absent(target)
    try:
        _write_copy(catalog, target)
    except (OSError, sqlite3.Error) as error:
        shutil.rmtree(target, ignore_errors=True)
        raise BackupError(f"Backup of {catalog} to {target} failed: {error}") from error
    logger.info("Catalog backed up to %s", target)
    return target


def restore_catalog(backup: Path, destination: Path) -> Path:
    _require_absent(destination)
    try:
        _write_copy(backup, destination)
    except (OSError, sqlite3.Error) as error:
        shutil.rmtree(destination, ignore_errors=True)
        raise BackupError(f"Restore of {backup} to {destination} failed: {error}") from error
    logger.info("Catalog restored to %s", destination)
    return destination


def _require_absent(target: Path) -> None:
    if target.exists():
        raise BackupError(f"Target already exists: {target}")


def list_backups(destination_root: Path) -> list[Path]:
    if not destination_root.is_dir():
        return []
    return sorted(path for path in destination_root.glob("*.darklab") if path.is_dir())


def _write_copy(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=False)
    _copy_database(database_file(source), target / DATABASE_NAME)
    _copy_optional_file(package_root(source) / SETTINGS_NAME, target / SETTINGS_NAME)
    _copy_optional_tree(package_root(source) / PREVIEWS_NAME, target / PREVIEWS_NAME)


def _copy_database(source: Path, target: Path) -> None:
    origin = sqlite3.connect(source)
    copy = sqlite3.connect(target)
    try:
        origin.backup(copy)
    finally:
        copy.close()
        origin.close()


def _copy_optional_file(source: Path, target: Path) -> None:
    if source.is_file():
        shutil.copyfile(source, target)


def _copy_optional_tree(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target)
        return
    target.mkdir()
