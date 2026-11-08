from pathlib import Path


def launch_is_allowed(width: int, height: int) -> bool:
    return width > 0 and height > 0


def log_directory(home: Path | None = None) -> Path:
    base = home if home is not None else Path.home()
    folder = base / "Library" / "Logs" / "DarkLab"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log_file(name: str = "darklab.log", home: Path | None = None) -> Path:
    return log_directory(home) / name
