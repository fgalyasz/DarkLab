from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from src.catalog.backup import BackupError, backup_catalog, default_backup_root
from src.catalog.locations import database_file
from src.catalog.schema_sql import (
    CURRENT_SCHEMA, FOLDERS_TABLE, PHOTO_COLUMN_STATEMENTS, PHOTO_COLUMNS_QUERY, PHOTO_TABLE,
    STORE_SCHEMA,
)

logger = logging.getLogger(__name__)


class CatalogMigrationError(ValueError):
    pass


def _upgrade_1_to_2(connection: sqlite3.Connection) -> None:
    connection.execute(PHOTO_TABLE)
    connection.execute(FOLDERS_TABLE)
    for column, statement in PHOTO_COLUMN_STATEMENTS.items():
        _add_missing_column(connection, column, statement)


def _add_missing_column(connection: sqlite3.Connection, column: str, statement: str) -> None:
    present = {str(row[1]) for row in connection.execute(PHOTO_COLUMNS_QUERY).fetchall()}
    if column not in present:
        connection.execute(statement)


MIGRATIONS: dict[int, Callable[[sqlite3.Connection], None]] = {1: _upgrade_1_to_2}


def migrate_catalog(catalog: Path, stored: str, moment: datetime | None = None) -> bool:
    version = _parse_version(catalog, stored)
    if version == CURRENT_SCHEMA:
        return False
    _require_upgrade_path(catalog, version)
    _back_up_first(catalog, moment)
    _apply_steps(catalog, version)
    logger.info("Catalog %s migrated from schema %s to %s", catalog, version, CURRENT_SCHEMA)
    return True


def _parse_version(catalog: Path, stored: str) -> int:
    try:
        return int(stored)
    except ValueError as error:
        raise CatalogMigrationError(f"Catalog {catalog} has an unreadable schema: {stored!r}") from error


def _require_upgrade_path(catalog: Path, version: int) -> None:
    if version > CURRENT_SCHEMA:
        raise CatalogMigrationError(
            f"Catalog {catalog} uses schema {version}; this DarkLab reads up to {CURRENT_SCHEMA}. "
            "Update DarkLab to open it."
        )
    missing = [step for step in range(version, CURRENT_SCHEMA) if step not in MIGRATIONS]
    if missing:
        raise CatalogMigrationError(f"Catalog {catalog} at schema {version} has no upgrade path")


def _back_up_first(catalog: Path, moment: datetime | None) -> None:
    try:
        backup_catalog(catalog, default_backup_root(catalog), moment)
    except BackupError as error:
        raise CatalogMigrationError(f"Upgrade of {catalog} refused, no backup was made: {error}") from error


def _apply_steps(catalog: Path, version: int) -> None:
    connection = sqlite3.connect(database_file(catalog), isolation_level=None)
    try:
        _run_in_transaction(connection, catalog, version)
    finally:
        connection.close()


def _run_in_transaction(connection: sqlite3.Connection, catalog: Path, version: int) -> None:
    connection.execute("BEGIN IMMEDIATE")
    try:
        _run_steps(connection, version)
        connection.execute("COMMIT")
    except sqlite3.Error as error:
        connection.execute("ROLLBACK")
        raise CatalogMigrationError(f"Upgrade of {catalog} from schema {version} failed: {error}") from error


def _run_steps(connection: sqlite3.Connection, version: int) -> None:
    for step in range(version, CURRENT_SCHEMA):
        MIGRATIONS[step](connection)
        connection.execute(STORE_SCHEMA, (str(step + 1),))
