import os
import sys
from pathlib import Path


def launch_is_allowed(width: int, height: int) -> bool:
    return width > 0 and height > 0


def log_directory(home: Path | None = None) -> Path:
    base = home if home is not None else Path.home()
    folder = _log_root(base)
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def _log_root(base: Path) -> Path:
    if sys.platform == "darwin":
        return base / "Library" / "Logs" / "DarkLab"
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", str(base / "AppData" / "Local"))
        return Path(local) / "DarkLab" / "logs"
    state = os.environ.get("XDG_STATE_HOME", str(base / ".local" / "state"))
    return Path(state) / "DarkLab" / "logs"


def log_file(name: str = "darklab.log", home: Path | None = None) -> Path:
    return log_directory(home) / name
