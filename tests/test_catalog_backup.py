import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from src.catalog.backup import (
    BackupError, backup_catalog, default_backup_root, list_backups, restore_catalog,
)
from src.catalog.database import create_catalog, open_catalog, original_paths
from src.catalog.index_images import list_index_images
from src.importing.originals import import_originals

MOMENT = datetime(2026, 10, 27, 20, 30, 15)


class BackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.folder = Path(tempfile.mkdtemp())
        self.catalog = create_catalog(self.folder / "shoot")
        self.original = self.folder / "a.png"
        Image.new("RGB", (8, 8), "red").save(self.original)
        import_originals(self.catalog, [self.original])

    def test_default_root_sits_beside_the_catalog(self) -> None:
        self.assertEqual(default_backup_root(self.catalog), self.folder / "shoot.darklab.backups")

    def test_backup_is_timestamped_and_has_the_photos(self) -> None:
        backup = backup_catalog(self.catalog, self.folder / "backups", MOMENT)
        self.assertEqual(backup.name, "shoot-20261027-203015.darklab")
        self.assertEqual(original_paths(open_catalog(backup)), [str(self.original)])
        self.assertEqual(len(list_index_images(backup)), 1)

    def test_backup_without_a_moment_uses_the_clock(self) -> None:
        backup = backup_catalog(self.catalog, self.folder / "backups")
        self.assertTrue(backup.name.startswith("shoot-"))

    def test_restore_brings_the_photos_back_and_keeps_originals(self) -> None:
        backup = backup_catalog(self.catalog, self.folder / "backups", MOMENT)
        restored = restore_catalog(backup, self.folder / "restored.darklab")
        self.assertEqual(original_paths(open_catalog(restored)), [str(self.original)])
        self.assertTrue(self.original.is_file())

    def test_restore_refuses_an_existing_target(self) -> None:
        backup = backup_catalog(self.catalog, self.folder / "backups", MOMENT)
        with self.assertRaises(BackupError):
            restore_catalog(backup, self.catalog)

    def test_restore_failure_leaves_no_partial_target(self) -> None:
        backup = backup_catalog(self.catalog, self.folder / "backups", MOMENT)
        target = self.folder / "broken.darklab"
        with patch("src.catalog.backup._copy_database", side_effect=sqlite3.Error("boom")):
            with self.assertRaises(BackupError):
                restore_catalog(backup, target)
        self.assertFalse(target.exists())

    def test_unwritable_destination_keeps_the_open_catalog(self) -> None:
        blocker = self.folder / "blocker"
        blocker.write_text("a file, not a folder", encoding="utf-8")
        with self.assertRaises(BackupError):
            backup_catalog(self.catalog, blocker / "backups", MOMENT)
        self.assertEqual(original_paths(open_catalog(self.catalog)), [str(self.original)])

    def test_failed_backup_removes_the_partial_copy(self) -> None:
        root = self.folder / "backups"
        with patch("src.catalog.backup._copy_database", side_effect=sqlite3.Error("boom")):
            with self.assertRaises(BackupError):
                backup_catalog(self.catalog, root, MOMENT)
        self.assertEqual(list_backups(root), [])

    def test_backup_in_the_same_second_keeps_the_earlier_backup(self) -> None:
        root = self.folder / "backups"
        first = backup_catalog(self.catalog, root, MOMENT)
        with self.assertRaises(BackupError):
            backup_catalog(self.catalog, root, MOMENT)
        self.assertEqual(original_paths(open_catalog(first)), [str(self.original)])

    def test_list_backups_is_oldest_first(self) -> None:
        root = self.folder / "backups"
        later = backup_catalog(self.catalog, root, datetime(2026, 10, 28, 9, 0, 0))
        earlier = backup_catalog(self.catalog, root, MOMENT)
        self.assertEqual(list_backups(root), [earlier, later])

    def test_list_backups_of_missing_root_is_empty(self) -> None:
        self.assertEqual(list_backups(self.folder / "none"), [])

    def test_catalog_without_settings_or_previews_still_backs_up(self) -> None:
        bare = self.folder / "bare.darklab"
        bare.mkdir()
        sqlite3.connect(bare / "catalog.sqlite").close()
        backup = backup_catalog(bare, self.folder / "backups", MOMENT)
        self.assertTrue((backup / "previews").is_dir())
        self.assertFalse((backup / "settings.json").exists())


if __name__ == "__main__":
    unittest.main()
