from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.release import update_apply, update_check, update_download, versioning
from src.release.downloads import LINUX_ASSET, MAC_ASSET, WINDOWS_ASSET
from src.release.update_check import ReleaseInfo, UpdateCheckError


class FakeResponse:
    def __init__(self, body: bytes, headers: dict | None = None) -> None:
        self._body = body
        self.headers = headers or {}

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            data = self._body
            self._body = b""
            return data
        data = self._body[:size]
        self._body = self._body[size:]
        return data

    def __enter__(self):
        return self

    def __exit__(self, *args) -> None:
        return None


class ProgressLog:
    def __init__(self) -> None:
        self.rows: list[tuple[int, int]] = []

    def __call__(self, done: int, total: int) -> None:
        self.rows.append((done, total))


def _payload(version: str, assets: dict[str, str]) -> dict:
    return {
        "tag_name": f"v{version}",
        "body": f"Notes for {version}",
        "assets": [
            {"name": name, "browser_download_url": url} for name, url in assets.items()
        ],
    }


class VersioningTests(unittest.TestCase):
    def test_read_and_compare(self) -> None:
        self.assertEqual(versioning.read_version_text(" 1.0.10\n"), "1.0.10")
        self.assertTrue(versioning.is_newer("1.0.11", "1.0.10"))
        self.assertFalse(versioning.is_newer("1.0.10", "1.0.10"))
        self.assertFalse(versioning.is_newer("1.0.9", "1.0.10"))

    def test_invalid_version(self) -> None:
        with self.assertRaises(ValueError):
            versioning.parse_semver("1.0")
        with self.assertRaises(ValueError):
            versioning.read_version_text("   ")

    def test_app_version_from_path(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "version.txt"
            path.write_text("2.3.4\n", encoding="utf-8")
            self.assertEqual(versioning.app_version(path), "2.3.4")


class UpdateCheckTests(unittest.TestCase):
    def test_parse_release_payload(self) -> None:
        info = update_check.parse_release_payload(
            _payload("1.2.3", {MAC_ASSET: "https://example/dmg"})
        )
        self.assertEqual(info.version, "1.2.3")
        self.assertEqual(info.tag, "v1.2.3")
        self.assertEqual(info.channel, "community")
        self.assertEqual(info.assets[MAC_ASSET], "https://example/dmg")

    def test_fetch_latest_release(self) -> None:
        body = json.dumps(_payload("9.9.9", {LINUX_ASSET: "https://example/tgz"})).encode()
        opener = MagicMock(return_value=FakeResponse(body))
        info = update_check.fetch_latest_release(opener)
        self.assertEqual(info.version, "9.9.9")
        opener.assert_called_once()

    def test_fetch_failure(self) -> None:
        opener = MagicMock(side_effect=TimeoutError("slow"))
        with self.assertRaises(UpdateCheckError):
            update_check.fetch_latest_release(opener)

    def test_platform_asset_name(self) -> None:
        self.assertEqual(update_check.platform_asset_name("Darwin"), MAC_ASSET)
        self.assertEqual(update_check.platform_asset_name("Windows"), WINDOWS_ASSET)
        self.assertEqual(update_check.platform_asset_name("Linux"), LINUX_ASSET)
        with self.assertRaises(UpdateCheckError):
            update_check.platform_asset_name("Plan9")

    def test_select_asset(self) -> None:
        info = ReleaseInfo("1.0.0", "v1.0.0", "", {WINDOWS_ASSET: "https://example/zip"})
        name, url = update_check.select_asset(info, "Windows")
        self.assertEqual(name, WINDOWS_ASSET)
        self.assertEqual(url, "https://example/zip")
        with self.assertRaises(UpdateCheckError):
            update_check.select_asset(info, "Darwin")

    def test_should_offer_update(self) -> None:
        info = ReleaseInfo("1.0.11", "v1.0.11", "", {}, "community")
        self.assertTrue(update_check.should_offer_update("1.0.10", info, ""))
        self.assertFalse(update_check.should_offer_update("1.0.10", info, "1.0.11"))
        self.assertFalse(update_check.should_offer_update("1.0.11", info, ""))
        other = ReleaseInfo("2.0.0", "v2.0.0", "", {}, "pro")
        self.assertFalse(update_check.should_offer_update("1.0.10", other, ""))


class UpdateDownloadTests(unittest.TestCase):
    def test_download_to_temp(self) -> None:
        payload = b"abc123"
        headers = {"Content-Length": str(len(payload))}
        opener = MagicMock(return_value=FakeResponse(payload, headers))
        progress = ProgressLog()
        with tempfile.TemporaryDirectory() as folder:
            dest = Path(folder) / "asset.bin"
            result = update_download.download_release_asset(
                "https://example/asset.bin",
                dest,
                on_progress=progress,
                opener=opener,
                chunk_size=2,
            )
            self.assertEqual(result.read_bytes(), payload)
            self.assertGreaterEqual(len(progress.rows), 1)


class UpdateApplyTests(unittest.TestCase):
    def test_open_download_page(self) -> None:
        with patch("src.release.update_apply.open_url") as open_url:
            update_apply.open_download_page("https://example/x")
            open_url.assert_called_once_with("https://example/x")

    def test_apply_darwin_copies_to_applications(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "DarkLab.dmg"
            archive.write_bytes(b"dmg")
            with patch("src.release.update_apply.subprocess.Popen") as popen:
                update_apply.apply_update(archive, "Darwin")
            popen.assert_called_once()
            script = Path(popen.call_args.args[0][1])
            text = script.read_text(encoding="utf-8")
            self.assertIn("hdiutil attach", text)
            self.assertIn("ditto", text)
            self.assertIn("/Applications/DarkLab.app", text)
            self.assertIn(f'open "/Applications/DarkLab.app"', text)

    def test_macos_script_targets_applications(self) -> None:
        script = update_apply._macos_script(
            42,
            Path("/tmp/DarkLab.dmg"),
            Path("/tmp/mnt"),
            update_apply.mac_install_destination(),
        )
        self.assertIn("/Applications/DarkLab.app", script)
        self.assertNotIn("\\Applications", script)
        self.assertIn("DarkLab.app", script)

    def test_mac_destination_is_posix(self) -> None:
        self.assertEqual(update_apply.mac_install_destination(), "/Applications/DarkLab.app")
        self.assertEqual(update_apply._posix(r"C:\tmp\mnt"), "C:/tmp/mnt")

    def test_apply_linux_writes_script(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "install" / "DarkLab"
            root.mkdir(parents=True)
            (root / "DarkLab").write_text("old", encoding="utf-8")
            archive = Path(folder) / "bundle.tar.gz"
            staging_src = Path(folder) / "payload"
            nested = staging_src / "DarkLab"
            nested.mkdir(parents=True)
            (nested / "DarkLab").write_text("new", encoding="utf-8")
            with tarfile.open(archive, "w:gz") as handle:
                handle.add(nested, arcname="DarkLab")
            with patch("src.release.update_apply.install_root", return_value=root):
                with patch("src.release.update_apply.subprocess.Popen") as popen:
                    with patch("src.release.update_apply.is_frozen_app", return_value=True):
                        update_apply.apply_update(archive, "Linux")
            popen.assert_called_once()
            script = Path(popen.call_args.args[0][1])
            self.assertTrue(script.exists())
            self.assertIn(str(root), script.read_text(encoding="utf-8"))

    def test_apply_windows_writes_script(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "install" / "DarkLab"
            root.mkdir(parents=True)
            (root / "DarkLab.exe").write_text("old", encoding="utf-8")
            archive = Path(folder) / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("DarkLab/DarkLab.exe", b"new")
            with patch("src.release.update_apply.install_root", return_value=root):
                with patch("src.release.update_apply.subprocess.Popen") as popen:
                    with patch("src.release.update_apply.is_frozen_app", return_value=True):
                        update_apply.apply_update(archive, "Windows")
            popen.assert_called_once()
            script = Path(popen.call_args.args[0][2])
            self.assertTrue(script.exists())

    def test_install_root_rejects_dev(self) -> None:
        with patch("src.release.update_apply.is_frozen_app", return_value=False):
            with self.assertRaises(UpdateCheckError):
                update_apply.install_root()


if __name__ == "__main__":
    unittest.main()
