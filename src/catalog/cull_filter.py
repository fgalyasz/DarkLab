from __future__ import annotations

from pathlib import Path

from src.catalog.marks import DEFAULTS

ANY = "any"
NO_MARKS = dict(DEFAULTS)


def matches_rating(marker: str, minimum: str) -> bool:
    if minimum == ANY:
        return True
    try:
        return int(marker or "0") >= int(minimum)
    except ValueError:
        return False


def matches_pick(marker: str, wanted: str) -> bool:
    return wanted == ANY or marker == wanted


def matches_color(marker: str, wanted: str) -> bool:
    return wanted == ANY or marker == wanted


def matches_marks(marks: dict[str, str], minimum_rating: str, pick: str, color: str) -> bool:
    return (
        matches_rating(marks.get("rating", "0"), minimum_rating)
        and matches_pick(marks.get("pick", "none"), pick)
        and matches_color(marks.get("color", "none"), color)
    )


def filter_by_marks(
    paths: list[Path],
    markers: dict[Path, dict[str, str]],
    minimum_rating: str = ANY,
    pick: str = ANY,
    color: str = ANY,
) -> list[Path]:
    return [
        path for path in paths
        if matches_marks(markers.get(path, NO_MARKS), minimum_rating, pick, color)
    ]
