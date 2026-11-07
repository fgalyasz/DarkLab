from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from src.catalog.capture_time import fill_missing_capture_times
from src.catalog.integrity import CatalogIntegrityError, require_healthy
from src.catalog.locations import database_file
from src.catalog.schema_sql import CATALOG_INDEXES, INDEX_NAMES_QUERY

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]

STEP_LABELS = (
    "Checking the Catalog",
    "Creating indexes",
    "Reading capture times",
    "Updating statistics",
    "Compacting free space",
    "Verifying the Catalog",
)
DONE_LABEL = "Catalog optimized"
ANALYZE = "ANALYZE"
VACUUM = "VACUUM"


class CatalogOptimizeError(ValueError):
    pass


@dataclass(frozen=True)
class OptimizeReport:
    created_indexes: tuple[str, ...]
    bytes_before: int
    bytes_after: int

    @property
    def reclaimed_bytes(self) -> int:
        return max(0, self.bytes_before - self.bytes_after)

    def describe(self) -> str:
        text = f"Catalog optimized: {self.reclaimed_bytes} byte(s) reclaimed."
        if self.created_indexes:
            text += f" Created {len(self.created_indexes)} index(es)."
        return text


class _Progress:
    def __init__(self, callback: ProgressCallback | None) -> None:
        self._callback = callback
        self._done = 0

    def advance(self) -> None:
        self._notify(STEP_LABELS[self._done])
        self._done += 1

    def finish(self) -> None:
        self._notify(DONE_LABEL)

    def _notify(self, label: str) -> None:
        if self._callback is not None:
            self._callback(self._done, len(STEP_LABELS), label)


def optimize_catalog(catalog: Path, progress: ProgressCallback | None = None) -> OptimizeReport:
    try:
        return _CatalogOptimizer(catalog, _Progress(progress)).run()
    except (sqlite3.Error, CatalogIntegrityError) as error:
        logger.error("Optimize of %s failed: %s", catalog, error)
        raise CatalogOptimizeError(f"Optimize of {catalog} failed: {error}") from error


class _CatalogOptimizer:
    def __init__(self, catalog: Path, progress: _Progress) -> None:
        self._catalog = catalog
        self._database = database_file(catalog)
        self._progress = progress
        self._created: tuple[str, ...] = ()

    def run(self) -> OptimizeReport:
        before = self._database.stat().st_size
        for step in self._steps():
            self._progress.advance()
            step()
        self._progress.finish()
        return OptimizeReport(self._created, before, self._database.stat().st_size)

    def _steps(self) -> tuple[Callable[[], None], ...]:
        return (self._check, self._index, self._capture, self._analyze, self._vacuum, self._verify)

    def _check(self) -> None:
        require_healthy(self._catalog)

    def _index(self) -> None:
        self._created = _create_indexes(self._database)

    def _capture(self) -> None:
        fill_missing_capture_times(self._catalog)

    def _analyze(self) -> None:
        _run_statement(self._database, ANALYZE)

    def _vacuum(self) -> None:
        _run_statement(self._database, VACUUM)

    def _verify(self) -> None:
        require_healthy(self._catalog, full=True)


def _create_indexes(database: Path) -> tuple[str, ...]:
    connection = sqlite3.connect(database)
    try:
        existing = _index_names(connection)
        for statement in CATALOG_INDEXES.values():
            connection.execute(statement)
        connection.commit()
    finally:
        connection.close()
    return tuple(name for name in CATALOG_INDEXES if name not in existing)


def _index_names(connection: sqlite3.Connection) -> set[str]:
    return {str(row[0]) for row in connection.execute(INDEX_NAMES_QUERY).fetchall()}


def _run_statement(database: Path, statement: str) -> None:
    connection = sqlite3.connect(database, isolation_level=None)
    try:
        connection.execute(statement)
    finally:
        connection.close()
