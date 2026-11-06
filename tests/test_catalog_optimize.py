import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication, QWidget

from src.catalog.database import create_catalog, open_catalog
from src.catalog.integrity import CatalogIntegrityError, check_integrity
from src.catalog.locations import database_file
from src.catalog.optimize import CatalogOptimizeError, OptimizeReport, STEP_LABELS, optimize_catalog
from src.catalog.schema_sql import CATALOG_INDEXES, INDEX_NAMES_QUERY
from src.ui.progress_reporter import ProgressReporter

APP = QApplication.instance() or QApplication([])
HEALTH_CHECK_TARGET = "src.catalog.optimize.require_healthy"
PHOTO_COUNT = 400
KEPT_PHOTOS = 20


def _query(catalog: Path, statement: str) -> list[tuple]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        return connection.execute(statement).fetchall()
    finally:
        connection.close()


def _execute(catalog: Path, statement: str) -> None:
    connection = sqlite3.connect(database_file(catalog))
    connection.execute(statement)
    connection.commit()
    connection.close()


def _fill_photos(catalog: Path, count: int) -> None:
    connection = sqlite3.connect(database_file(catalog))
    connection.executemany(
        "INSERT INTO photos (original_path, content_hash) VALUES (?, ?)",
        [(f"/shoot/{index}.jpg", f"hash-{index}" * 40) for index in range(count)],
    )
    connection.commit()
    connection.close()


def _index_names(catalog: Path) -> set[str]:
    return {str(row[0]) for row in _query(catalog, INDEX_NAMES_QUERY)}


class OptimizeFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.catalog = create_catalog(self.root / "shoot")
        _fill_photos(self.catalog, PHOTO_COUNT)
        _execute(self.catalog, f"DELETE FROM photos WHERE id > {KEPT_PHOTOS}")


class OptimizeCatalogTests(OptimizeFixture):
    def test_indexes_are_missing_before_and_present_after(self) -> None:
        self.assertTrue(set(CATALOG_INDEXES).isdisjoint(_index_names(self.catalog)))
        report = optimize_catalog(self.catalog)
        self.assertTrue(set(CATALOG_INDEXES) <= _index_names(self.catalog))
        self.assertEqual(set(report.created_indexes), set(CATALOG_INDEXES))

    def test_free_pages_are_reclaimed(self) -> None:
        self.assertGreater(_query(self.catalog, "PRAGMA freelist_count")[0][0], 0)
        report = optimize_catalog(self.catalog)
        self.assertEqual(_query(self.catalog, "PRAGMA freelist_count")[0][0], 0)
        self.assertGreater(report.reclaimed_bytes, 0)

    def test_integrity_still_passes_and_rows_are_kept(self) -> None:
        optimize_catalog(self.catalog)
        self.assertTrue(check_integrity(self.catalog, full=True).healthy)
        self.assertEqual(_query(self.catalog, "SELECT count(*) FROM photos")[0][0], KEPT_PHOTOS)

    def test_second_run_creates_no_index(self) -> None:
        optimize_catalog(self.catalog)
        self.assertEqual(optimize_catalog(self.catalog).created_indexes, ())

    def test_open_still_works_after_optimize(self) -> None:
        optimize_catalog(self.catalog)
        self.assertEqual(open_catalog(self.catalog), self.catalog)

    def test_progress_reports_every_step_then_done(self) -> None:
        calls: list[tuple[int, int, str]] = []
        optimize_catalog(self.catalog, lambda done, total, label: calls.append((done, total, label)))
        self.assertEqual([call[2] for call in calls[:-1]], list(STEP_LABELS))
        self.assertEqual([call[0] for call in calls], [0, 1, 2, 3, 4, 5])
        self.assertEqual(calls[-1][:2], (len(STEP_LABELS), len(STEP_LABELS)))


class OptimizeFailureTests(OptimizeFixture):
    def test_damaged_catalog_is_refused_and_not_touched(self) -> None:
        database_file(self.catalog).write_bytes(b"torn" * 500)
        with self.assertRaises(CatalogOptimizeError) as context:
            optimize_catalog(self.catalog)
        self.assertIn("failed", str(context.exception))
        self.assertEqual(database_file(self.catalog).read_bytes(), b"torn" * 500)

    def test_sqlite_failure_is_reported_with_the_catalog_path(self) -> None:
        with patch("src.catalog.optimize._run_statement", side_effect=sqlite3.OperationalError("locked")):
            with self.assertRaises(CatalogOptimizeError) as context:
                optimize_catalog(self.catalog)
        self.assertIn(str(self.catalog), str(context.exception))

    def test_failed_verification_is_reported(self) -> None:
        with patch(HEALTH_CHECK_TARGET, side_effect=[None, CatalogIntegrityError("bad")]):
            with self.assertRaises(CatalogOptimizeError):
                optimize_catalog(self.catalog)


class OptimizeReportTests(unittest.TestCase):
    def test_describe_mentions_reclaimed_bytes_and_indexes(self) -> None:
        text = OptimizeReport(("idx_a",), 5000, 3000).describe()
        self.assertIn("2000 byte(s) reclaimed", text)
        self.assertIn("Created 1 index(es)", text)

    def test_describe_without_indexes_and_growth_never_negative(self) -> None:
        report = OptimizeReport((), 100, 200)
        self.assertEqual(report.reclaimed_bytes, 0)
        self.assertNotIn("Created", report.describe())


class ProgressReporterTests(unittest.TestCase):
    def test_reporter_shows_label_and_value(self) -> None:
        parent = QWidget()
        reporter = ProgressReporter(parent, "Optimize Catalog")
        reporter(2, 5, "Creating indexes")
        self.assertEqual(reporter.text, "Creating indexes")
        self.assertEqual(reporter.value, 2)
        reporter.close()
        parent.close()


if __name__ == "__main__":
    unittest.main()
