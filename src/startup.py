import os
import sys
from pathlib import Path


def launch_is_allowed(width: int, height: int) -> bool:
    return width > 0 and height > 0


def log_directory(home: Path | None = None) -> Path:
    folder = _log_root(home)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _log_root(home: Path | None) -> Path:
    base = home if home is not None else Path.home()
    if sys.platform == "darwin":
        return base / "Library" / "Logs" / "DarkLab"
    if sys.platform == "win32":
        return _windows_log_root(base, home is None)
    return _linux_log_root(base, home is None)


def _windows_log_root(base: Path, use_env: bool) -> Path:
    default = str(base / "AppData" / "Local")
    local = os.environ.get("LOCALAPPDATA", default) if use_env else default
    return Path(local) / "DarkLab" / "logs"


def _linux_log_root(base: Path, use_env: bool) -> Path:
    default = str(base / ".local" / "state")
    state = os.environ.get("XDG_STATE_HOME", default) if use_env else default
    return Path(state) / "DarkLab" / "logs"


def log_file(name: str = "darklab.log", home: Path | None = None) -> Path:
    return log_directory(home) / name
