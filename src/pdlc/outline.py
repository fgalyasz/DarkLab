from __future__ import annotations

import re

EPIC_HEADING = re.compile(r"^## Epic (\d+): (.+)$")
STORY_HEADING = re.compile(r"^### Story (\d+\.\d+): (.+)$")


def match_heading(line: str) -> tuple[str, str, str] | None:
    epic = EPIC_HEADING.match(line)
    if epic is not None:
        return ("epic", epic.group(1), epic.group(2))
    return story_heading(line)


def story_heading(line: str) -> tuple[str, str, str] | None:
    story = STORY_HEADING.match(line)
    if story is None:
        return None
    return ("story", story.group(1), story.group(2))


def start_item(kind: str, number: str, title: str) -> dict[str, str]:
    return {"kind": kind, "number": number, "title": title, "body": ""}


def append_body(current: dict[str, str] | None, line: str) -> None:
    if current is None:
        return
    current["body"] = f"{current['body']}{line}\n"


def finish(items: list[dict[str, str]], current: dict[str, str] | None) -> None:
    if current is None:
        return
    current["body"] = current["body"].strip()
    items.append(current)


def take_line(items: list[dict[str, str]], current: dict[str, str] | None, line: str) -> dict[str, str] | None:
    matched = match_heading(line)
    if matched is None:
        append_body(current, line)
        return current
    finish(items, current)
    return start_item(matched[0], matched[1], matched[2])


def parse_outline(text: str) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        current = take_line(items, current, line)
    finish(items, current)
    return items


def parent_key(item: dict[str, str]) -> str | None:
    if item["kind"] == "epic":
        return None
    return item["number"].split(".")[0]
