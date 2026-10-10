from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pdlc.outline import parent_key, parse_outline

EPICS = ROOT / "_bmad-output" / "planning-artifacts" / "epics.md"
META_DIR = ROOT / "docs" / "pdlc"
PROJECT_PATH = META_DIR / "project.json"
MAP_PATH = META_DIR / "issue-map.json"
REPO = "fgalyasz/DarkLab"
OWNER = "fgalyasz"
SOURCE = (
    "https://github.com/fgalyasz/DarkLab/blob/main/"
    "_bmad-output/planning-artifacts/epics.md"
)
PRD = (
    "https://github.com/fgalyasz/DarkLab/blob/main/"
    "_bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/prd.md"
)


def run(args: list[str]) -> str:
    completed = subprocess.run(args, check=True, capture_output=True, text=True)
    return completed.stdout.strip()


def create_label(name: str, color: str) -> None:
    subprocess.run(
        ["gh", "label", "create", name, "--repo", REPO, "--color", color, "--force"],
        check=True,
    )


def ensure_labels() -> None:
    create_label("epic", "1D4ED8")
    create_label("story", "0F766E")


def read_json(path: Path) -> dict[str, str]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def create_project() -> dict[str, str]:
    raw = run(["gh", "project", "create", "--owner", OWNER, "--title", "DarkLab", "--format", "json"])
    created = json.loads(raw)
    meta = project_meta(created)
    write_json(PROJECT_PATH, meta)
    return meta


def project_meta(created: dict[str, object]) -> dict[str, str]:
    return {
        "owner": OWNER,
        "repo": REPO,
        "project_number": str(created["number"]),
        "url": str(created.get("url", "")),
    }


def load_project() -> dict[str, str]:
    if PROJECT_PATH.exists():
        return read_json(PROJECT_PATH)
    return create_project()


def load_map() -> dict[str, str]:
    if MAP_PATH.exists():
        return read_json(MAP_PATH)
    return {}


def issue_title(item: dict[str, str]) -> str:
    prefix = "[EPIC]" if item["kind"] == "epic" else "[STORY]"
    return f"{prefix} {item['number']}. {item['title']}"


def issue_body(item: dict[str, str]) -> str:
    return f"Source: {SOURCE}\n\nPRD: {PRD}\n\n{item['body']}\n"


def body_file(body: str) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    handle.write(body)
    handle.close()
    return handle.name


def create_command(item: dict[str, str], parent: str | None) -> list[str]:
    command = [
        "gh", "issue", "create", "--repo", REPO,
        "--title", issue_title(item),
        "--body-file", body_file(issue_body(item)),
        "--label", item["kind"],
    ]
    return with_parent(command, parent)


def with_parent(command: list[str], parent: str | None) -> list[str]:
    if parent is None:
        return command
    return command + ["--parent", parent]


def issue_number(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def add_to_project(meta: dict[str, str], url: str) -> None:
    number = meta["project_number"]
    owner = meta["owner"]
    add_item(number, owner, url)
    set_status(number, owner, url)


def add_item(number: str, owner: str, url: str) -> None:
    completed = subprocess.run(
        ["gh", "project", "item-add", number, "--owner", owner, "--url", url],
        capture_output=True,
        text=True,
    )
    accept_existing(completed)


def accept_existing(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.returncode == 0:
        return
    if "already exists" in completed.stderr:
        return
    completed.check_returncode()


def set_status(number: str, owner: str, url: str) -> None:
    subprocess.run(
        ["gh", "project", "item-edit", number, "--owner", owner, "--url", url, "--field", "Status", "--value", "Todo"],
        check=True,
    )


def parent_number(mapped: dict[str, str], item: dict[str, str]) -> str | None:
    key = parent_key(item)
    if key is None:
        return None
    return mapped[key]


def seed_item(meta: dict[str, str], mapped: dict[str, str], item: dict[str, str]) -> None:
    if item["number"] in mapped:
        return
    url = run(create_command(item, parent_number(mapped, item)))
    mapped[item["number"]] = issue_number(url)
    write_json(MAP_PATH, mapped)
    add_to_project(meta, url)


def seed() -> None:
    ensure_labels()
    meta = load_project()
    mapped = load_map()
    for item in parse_outline(EPICS.read_text(encoding="utf-8")):
        seed_item(meta, mapped, item)


if __name__ == "__main__":
    seed()
