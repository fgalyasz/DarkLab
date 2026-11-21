from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from webbrowser import open as open_url

from src.release.update_check import UpdateCheckError

MAC_APPLICATIONS_APP = Path("/Applications/DarkLab.app")
MAC_APP_NAME = "DarkLab.app"


def is_frozen_app() -> bool:
    return bool(getattr(sys, "frozen", False))


def install_root() -> Path:
    if is_frozen_app():
        return Path(sys.executable).resolve().parent
    raise UpdateCheckError("In-place update requires a packaged DarkLab build")


def apply_update(archive: Path, system: str | None = None) -> None:
    name = (system or platform.system()).lower()
    if name == "darwin":
        _apply_macos(archive)
        return
    if name == "windows":
        _apply_windows(archive)
        return
    if name == "linux":
        _apply_linux(archive)
        return
    raise UpdateCheckError(f"Unsupported platform for apply: {name}")


def open_downloaded_installer(archive: Path, system: str | None = None) -> None:
    name = (system or platform.system()).lower()
    if name == "darwin":
        subprocess.Popen(["open", str(archive)])
        return
    open_url(archive.as_uri())


def open_download_page(url: str) -> None:
    open_url(url)


def mac_install_destination() -> Path:
    return MAC_APPLICATIONS_APP


def _apply_macos(archive: Path) -> None:
    staging = Path(tempfile.mkdtemp(prefix="darklab-update-"))
    mount = staging / "mnt"
    mount.mkdir()
    script = staging / "replace.sh"
    script.write_text(
        _macos_script(os.getpid(), archive, mount, mac_install_destination()),
        encoding="utf-8",
    )
    script.chmod(0o755)
    subprocess.Popen(["/bin/bash", str(script)], close_fds=True)


def _apply_windows(archive: Path) -> None:
    root = install_root()
    staging = Path(tempfile.mkdtemp(prefix="darklab-update-"))
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(staging)
    payload = _bundle_payload(staging, "DarkLab.exe")
    script = staging / "replace.bat"
    script.write_text(_windows_script(os.getpid(), payload, root), encoding="utf-8")
    subprocess.Popen(["cmd", "/c", str(script)], close_fds=True)


def _apply_linux(archive: Path) -> None:
    root = install_root()
    staging = Path(tempfile.mkdtemp(prefix="darklab-update-"))
    with tarfile.open(archive, "r:gz") as bundle:
        bundle.extractall(staging, filter="data")
    payload = _bundle_payload(staging, "DarkLab")
    script = staging / "replace.sh"
    script.write_text(_linux_script(os.getpid(), payload, root), encoding="utf-8")
    script.chmod(0o755)
    subprocess.Popen(["/bin/bash", str(script)], close_fds=True)


def _bundle_payload(staging: Path, executable_name: str) -> Path:
    direct = staging / executable_name
    if direct.exists():
        return staging
    nested = staging / "DarkLab"
    if (nested / executable_name).exists():
        return nested
    raise UpdateCheckError(f"Update archive missing {executable_name}")


def _macos_script(pid: int, dmg: Path, mount: Path, destination: Path) -> str:
    return (
        f"#!/bin/bash\n"
        f"set -euo pipefail\n"
        f"while kill -0 {pid} 2>/dev/null; do sleep 1; done\n"
        f"hdiutil attach \"{dmg}\" -nobrowse -readonly -mountpoint \"{mount}\"\n"
        f"APP=\"$(find \"{mount}\" -maxdepth 2 -name '{MAC_APP_NAME}' -type d | head -n 1)\"\n"
        f"if [[ -z \"$APP\" ]]; then hdiutil detach \"{mount}\" -quiet || true; exit 1; fi\n"
        f"rm -rf \"{destination}\"\n"
        f"ditto \"$APP\" \"{destination}\"\n"
        f"hdiutil detach \"{mount}\" -quiet || true\n"
        f"open \"{destination}\"\n"
    )


def _windows_script(pid: int, payload: Path, root: Path) -> str:
    return (
        f"@echo off\n"
        f":wait\n"
        f"tasklist /FI \"PID eq {pid}\" | find \"{pid}\" >nul\n"
        f"if not errorlevel 1 (\n"
        f"  timeout /t 1 /nobreak >nul\n"
        f"  goto wait\n"
        f")\n"
        f"robocopy \"{payload}\" \"{root}\" /E /IS /IT >nul\n"
        f"start \"\" \"{root / 'DarkLab.exe'}\"\n"
    )


def _linux_script(pid: int, payload: Path, root: Path) -> str:
    return (
        f"#!/bin/bash\n"
        f"while kill -0 {pid} 2>/dev/null; do sleep 1; done\n"
        f"rm -rf \"{root}.bak\"\n"
        f"mv \"{root}\" \"{root}.bak\"\n"
        f"mkdir -p \"{root.parent}\"\n"
        f"cp -a \"{payload}\" \"{root}\"\n"
        f"\"{root / 'DarkLab'}\" &\n"
        f"rm -rf \"{root}.bak\"\n"
    )


def cleanup_path(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
        return
    if path.exists():
        path.unlink(missing_ok=True)
