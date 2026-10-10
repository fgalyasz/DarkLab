from pathlib import Path


def pictures_directory() -> Path:
    pictures = Path.home() / "Pictures"
    if pictures.is_dir():
        return pictures
    return Path.home()


def existing_paths(stored: object) -> list[Path]:
    if not isinstance(stored, list):
        return []
    return [Path(item) for item in stored if Path(str(item)).is_file()]


def merge_catalog_paths(stored: object, selected: list[Path]) -> list[str]:
    current = stored if isinstance(stored, list) else []
    ordered = [str(item) for item in current]
    ordered.extend(str(path) for path in selected)
    return list(dict.fromkeys(ordered))


def filter_paths(paths: list[Path], text: str) -> list[Path]:
    query = text.strip().lower()
    if not query:
        return list(paths)
    return [path for path in paths if query in path.name.lower()]


def sort_paths(paths: list[Path], mode: str) -> list[Path]:
    if mode == "name":
        return sorted(paths, key=_name_key)
    if mode == "time":
        return sorted(paths, key=_time_key, reverse=True)
    return list(paths)


def keyword_tokens(text: str) -> list[str]:
    chunks = text.replace(",", "\n").splitlines()
    return [chunk.strip() for chunk in chunks if chunk.strip()]


def matches_rating(marker: str, minimum: str) -> bool:
    if minimum == "any":
        return True
    try:
        return int(marker or "0") >= int(minimum)
    except ValueError:
        return False


def _name_key(path: Path) -> str:
    return path.name.lower()


def _time_key(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def previous_import_directory(settings: object) -> Path | None:
    if not isinstance(settings, dict):
        return None
    presets = settings.get("destination_presets", {})
    active = str(settings.get("active_destination_preset", "Default"))
    preset = presets.get(active, {}) if isinstance(presets, dict) else {}
    target = str(preset.get("target_root", "")).strip()
    if target and Path(target).is_dir():
        return Path(target)
    return None
