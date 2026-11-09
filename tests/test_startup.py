import sys
import tempfile
import unittest
from pathlib import Path

from src.startup import launch_is_allowed, log_directory, log_file

ROOT = Path(__file__).resolve().parents[1]
BUILD_DMG = ROOT / "scripts" / "build_dmg.sh"
BUILD_LINUX = ROOT / "scripts" / "build_linux.sh"


def _expected_log_root(home: Path) -> Path:
    if sys.platform == "darwin":
        return home / "Library" / "Logs" / "DarkLab"
    if sys.platform == "win32":
        return home / "AppData" / "Local" / "DarkLab" / "logs"
    return home / ".local" / "state" / "DarkLab" / "logs"


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
            self.assertEqual(folder, _expected_log_root(home))
            self.assertTrue(folder.is_dir())

    def test_log_file_defaults_to_darklab_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            root = _expected_log_root(home)
            target = log_file(home=home)
            self.assertEqual(target, root / "darklab.log")
            extra = log_file("import_dialog.log", home)
            self.assertEqual(extra, root / "import_dialog.log")
            self.assertTrue(extra.parent.is_dir())

    def test_build_dmg_collects_pyexiv2_binaries(self) -> None:
        script = BUILD_DMG.read_text(encoding="utf-8")
        self.assertIn("--collect-binaries pyexiv2", script)

    def test_build_linux_collects_pyexiv2_binaries(self) -> None:
        script = BUILD_LINUX.read_text(encoding="utf-8")
        self.assertIn("--collect-binaries pyexiv2", script)
