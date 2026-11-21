from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from typing import Callable
from urllib.error import URLError
from urllib.request import Request

from src.release.downloads import GITHUB_REPO, LINUX_ASSET, MAC_ASSET, WINDOWS_ASSET
from src.release.http import open_url
from src.release.versioning import is_newer, parse_semver, read_version_text


class UpdateCheckError(Exception):
    pass


@dataclass(frozen=True)
class ReleaseInfo:
    version: str
    tag: str
    notes: str
    assets: dict[str, str]
    channel: str = "community"


def latest_api_url(repo: str = GITHUB_REPO) -> str:
    return f"https://api.github.com/repos/{repo}/releases/latest"


def parse_release_payload(payload: dict) -> ReleaseInfo:
    tag = str(payload.get("tag_name", ""))
    version = read_version_text(tag[1:] if tag.startswith("v") else tag)
    assets = {
        str(item["name"]): str(item["browser_download_url"])
        for item in payload.get("assets", [])
        if "name" in item and "browser_download_url" in item
    }
    return ReleaseInfo(version, tag, str(payload.get("body", "")), assets)


def fetch_latest_release(opener: Callable = open_url) -> ReleaseInfo:
    request = Request(
        latest_api_url(),
        headers={"Accept": "application/vnd.github+json", "User-Agent": "DarkLab-Updater"},
    )
    try:
        with opener(request, timeout=20) as response:
            return parse_release_payload(json.loads(response.read().decode("utf-8")))
    except (URLError, TimeoutError, json.JSONDecodeError, ValueError, KeyError, TypeError) as error:
        raise UpdateCheckError(f"Could not check for updates: {error}") from error


def platform_asset_name(system: str | None = None) -> str:
    name = (system or platform.system()).lower()
    if name == "darwin":
        return MAC_ASSET
    if name == "windows":
        return WINDOWS_ASSET
    if name == "linux":
        return LINUX_ASSET
    raise UpdateCheckError(f"Unsupported platform for updates: {name}")


def select_asset(info: ReleaseInfo, system: str | None = None) -> tuple[str, str]:
    filename = platform_asset_name(system)
    url = info.assets.get(filename)
    if url is None:
        raise UpdateCheckError(f"Release {info.version} has no asset {filename}")
    return filename, url


def should_offer_update(current: str, latest: ReleaseInfo, skipped: str) -> bool:
    parse_semver(current)
    if skipped != "" and skipped == latest.version:
        return False
    if latest.channel != "community":
        return False
    return is_newer(latest.version, current)
