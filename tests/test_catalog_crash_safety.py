import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from src.catalog.atomic_file import write_bytes_atomic, write_text_atomic
from src.catalog.catalog_settings import read_catalog_setting, write_catalog_setting
from src.catalog.database import create_catalog, open_catalog
from src.catalog.index_images import read_index_image, write_index_image
from src.catalog.integrity import check_integrity
from src.catalog.locations import database_file, preview_directory, settings_file

ORIGINAL_HASH = "a" * 200
INTERRUPTED_HASH = "z" * 200
PHOTO_COUNT = 3000
REPLACE_TARGET = "src.catalog.atomic_file.os.replace"
KILLED_WRITER = """
import os
import sqlite3
import sys

connection = sqlite3.connect(sys.argv[1])
connection.execute("PRAGMA cache_size=10")
connection.execute("UPDATE photos SET content_hash = ?", (sys.argv[2],))
os._exit(1)
"""


def _filled_catalog() -> Path:
    catalog = create_catalog(Path(tempfile.mkdtemp()) / "shoot")
    connection = sqlite3.connect(database_file(catalog))
    connection.executemany(
        "INSERT INTO photos (original_path, content_hash) VALUES (?, ?)",
        [(f"/shoot/{index}.jpg", ORIGINAL_HASH) for index in range(PHOTO_COUNT)],
    )
    connection.commit()
    connection.close()
    return catalog


def _kill_writer_mid_update(catalog: Path) -> None:
    command = [sys.executable, "-c", KILLED_WRITER, str(database_file(catalog)), INTERRUPTED_HASH]
    subprocess.run(command, check=False)


def _journal(catalog: Path) -> Path:
    database = database_file(catalog)
    return database.with_name(database.name + "-journal")


def _stored_hashes(catalog: Path) -> set[str]:
    connection = sqlite3.connect(database_file(catalog))
    try:
        return {str(row[0]) for row in connection.execute("SELECT content_hash FROM photos")}
    finally:
        connection.close()


class KilledWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = _filled_catalog()
        _kill_writer_mid_update(self.catalog)

    def test_killed_write_leaves_a_journal_behind(self) -> None:
        self.assertTrue(_journal(self.catalog).is_file())

    def test_reopen_shows_the_previous_commit(self) -> None:
        self.assertEqual(open_catalog(self.catalog), self.catalog)
        self.assertEqual(_stored_hashes(self.catalog), {ORIGINAL_HASH})
        self.assertFalse(_journal(self.catalog).exists())

    def test_integrity_check_recovers_instead_of_reporting_damage(self) -> None:
        report = check_integrity(self.catalog, full=True)
        self.assertTrue(report.healthy, report.describe())

    def test_recovery_logs_a_warning(self) -> None:
        with self.assertLogs("src.catalog.integrity", level="WARNING") as captured:
            check_integrity(self.catalog)
        self.assertIn("interrupted", captured.output[0])


class RecoveryEdgeTests(unittest.TestCase):
    def test_missing_database_is_not_created_by_recovery(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "shoot")
        database_file(catalog).unlink()
        self.assertFalse(check_integrity(catalog).healthy)
        self.assertFalse(database_file(catalog).exists())

    def test_healthy_catalog_logs_no_recovery_warning(self) -> None:
        catalog = create_catalog(Path(tempfile.mkdtemp()) / "shoot")
        with self.assertNoLogs("src.catalog.integrity", level="WARNING"):
            check_integrity(catalog)


class AtomicFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.target = self.folder / "value.txt"

    def test_text_is_written_whole(self) -> None:
        write_text_atomic(self.target, "hello\n")
        self.assertEqual(self.target.read_text(encoding="utf-8"), "hello\n")
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()), ["value.txt"])

    def test_bytes_replace_the_previous_content(self) -> None:
        write_bytes_atomic(self.target, b"one")
        write_bytes_atomic(self.target, b"two")
        self.assertEqual(self.target.read_bytes(), b"two")

    def test_failed_replace_keeps_the_previous_content_and_cleans_up(self) -> None:
        write_bytes_atomic(self.target, b"one")
        with patch(REPLACE_TARGET, side_effect=OSError("killed")):
            with self.assertRaises(OSError):
                write_bytes_atomic(self.target, b"two")
        self.assertEqual(self.target.read_bytes(), b"one")
        self.assertEqual(sorted(path.name for path in self.folder.iterdir()), ["value.txt"])

    def test_failed_write_to_a_missing_folder_is_raised(self) -> None:
        with self.assertRaises(OSError):
            write_bytes_atomic(self.folder / "missing" / "value.txt", b"one")


class CatalogFileWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = create_catalog(Path(tempfile.mkdtemp()) / "shoot")

    def test_interrupted_setting_write_keeps_the_previous_setting(self) -> None:
        write_catalog_setting(self.catalog, "preview_size", "standard")
        with patch(REPLACE_TARGET, side_effect=OSError("killed")):
            with self.assertRaises(OSError):
                write_catalog_setting(self.catalog, "preview_size", "large")
        self.assertEqual(read_catalog_setting(self.catalog, "preview_size"), "standard")
        self.assertEqual(sorted(path.name for path in self.catalog.iterdir() if path.name.endswith(".tmp")), [])

    def test_interrupted_index_image_write_keeps_the_previous_image(self) -> None:
        write_index_image(self.catalog, 1, b"first")
        with patch(REPLACE_TARGET, side_effect=OSError("killed")):
            with self.assertRaises(OSError):
                write_index_image(self.catalog, 1, b"second")
        self.assertEqual(read_index_image(self.catalog, 1), b"first")
        self.assertEqual([path.name for path in preview_directory(self.catalog).iterdir()], ["1.jpg"])

    def test_new_catalog_settings_file_is_a_complete_json_object(self) -> None:
        self.assertEqual(settings_file(self.catalog).read_text(encoding="utf-8"), "{}\n")


if __name__ == "__main__":
    unittest.main()
