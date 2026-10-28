from __future__ import annotations

from src.catalog.marks import DEFAULTS

STAR_COUNT = 5
PICK_WORDS = {"accepted": "Pick", "rejected": "Rejected"}


def marks_text(marks: dict[str, str]) -> str:
    parts = [_stars(marks), _pick(marks), _color(marks)]
    return "   ".join(part for part in parts if part)


def _stars(marks: dict[str, str]) -> str:
    count = int(marks.get("rating", DEFAULTS["rating"]))
    return "★" * count + "☆" * (STAR_COUNT - count)


def _pick(marks: dict[str, str]) -> str:
    return PICK_WORDS.get(marks.get("pick", DEFAULTS["pick"]), "")


def _color(marks: dict[str, str]) -> str:
    color = marks.get("color", DEFAULTS["color"])
    if color == DEFAULTS["color"]:
        return ""
    return color.capitalize()
