from pathlib import Path
import tempfile
import unittest

from src.startup import launch_is_allowed, log_directory, log_file

ROOT = Path(__file__).resolve().parents[1]
BUILD_DMG = ROOT / "scripts" / "build_dmg.sh"


class StartupTests(unittest.TestCase):
    def test_small_display_can_launch(self) -> None:
        self.assertTrue(launch_is_allowed(1280, 800))

    def test_missing_display_cannot_launch(self) -> None:
        self.assertFalse(launch_is_allowed(0, 800))
        self.assertFalse(launch_is_allowed(1280, 0))

    def test_log_directory_creates_user_logs_folder(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            folder = log_directory(home)
            self.assertEqual(folder, home / "Library" / "Logs" / "DarkLab")
            self.assertTrue(folder.is_dir())

    def test_log_file_defaults_to_darklab_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            target = log_file(home=home)
            self.assertEqual(target, home / "Library" / "Logs" / "DarkLab" / "darklab.log")
            self.assertEqual(log_file("import_dialog.log", home), folder := home / "Library" / "Logs" / "DarkLab" / "import_dialog.log")
            self.assertTrue(folder.parent.is_dir())

    def test_build_dmg_collects_pyexiv2_binaries(self) -> None:
        script = BUILD_DMG.read_text(encoding="utf-8")
        self.assertIn("--collect-binaries pyexiv2", script)
