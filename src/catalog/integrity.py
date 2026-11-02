from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from src.catalog.locations import database_file

logger = logging.getLogger(__name__)

QUICK_CHECK = "PRAGMA quick_check"
FULL_CHECK = "PRAGMA integrity_check"
HEALTHY_ANSWER = "ok"
MAX_REPORTED_PROBLEMS = 5


class CatalogIntegrityError(ValueError):
    pass


@dataclass(frozen=True)
class IntegrityReport:
    catalog: Path
    full: bool
    problems: tuple[str, ...]

    @property
    def healthy(self) -> bool:
        return not self.problems

    def describe(self) -> str:
        kind = "full" if self.full else "quick"
        if self.healthy:
            return f"Catalog {self.catalog} passed the {kind} integrity check."
        shown = "; ".join(self.problems[:MAX_REPORTED_PROBLEMS])
        return f"Catalog {self.catalog} failed the {kind} integrity check: {shown}"


def check_integrity(catalog: Path, full: bool = False) -> IntegrityReport:
    problems = _collect_problems(database_file(catalog), FULL_CHECK if full else QUICK_CHECK)
    report = IntegrityReport(catalog, full, problems)
    if not report.healthy:
        logger.error(report.describe())
    return report


def require_healthy(catalog: Path, full: bool = False) -> IntegrityReport:
    report = check_integrity(catalog, full)
    if not report.healthy:
        raise CatalogIntegrityError(report.describe())
    return report


def _collect_problems(database: Path, pragma: str) -> tuple[str, ...]:
    try:
        answers = _run_pragma(database, pragma)
    except sqlite3.DatabaseError as error:
        return (f"{error}",)
    return tuple(answer for answer in answers if answer != HEALTHY_ANSWER)


def _run_pragma(database: Path, pragma: str) -> list[str]:
    connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
    try:
        return [str(row[0]) for row in connection.execute(pragma).fetchall()]
    finally:
        connection.close()
