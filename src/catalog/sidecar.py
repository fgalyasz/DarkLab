from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path

import pyexiv2

logger = logging.getLogger(__name__)

NAMESPACE_URI = "https://tenprint.software/ns/darklab/1.0/"
NAMESPACE_PREFIX = "darklab"
KEY_PREFIX = f"Xmp.{NAMESPACE_PREFIX}."
EMPTY_SIDECAR = (
    '<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
    '<x:xmpmeta xmlns:x="adobe:ns:meta/">'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"/>'
    '</x:xmpmeta><?xpacket end="w"?>'
)


class SidecarError(OSError):
    pass


def sidecar_path(original: Path) -> Path:
    return original.with_suffix(".xmp")


def write_sidecar(original: Path, settings: dict[str, str]) -> Path:
    target = sidecar_path(original)
    staged = target.with_name(f"{target.stem}.darklab-tmp.xmp")
    _stage_copy(target, staged)
    try:
        _merge_settings(staged, target, settings)
        os.replace(staged, target)
    finally:
        staged.unlink(missing_ok=True)
    return target


def read_sidecar(original: Path) -> dict[str, str]:
    target = sidecar_path(original)
    if not target.is_file():
        return {}
    try:
        return _develop_keys(_read_tags(target))
    except (RuntimeError, OSError) as error:
        logger.warning("Sidecar unreadable at %s: %s", target, error)
        return {}


def _stage_copy(target: Path, staged: Path) -> None:
    if target.is_file():
        shutil.copyfile(target, staged)
        return
    staged.write_text(EMPTY_SIDECAR, encoding="utf-8")


def _merge_settings(staged: Path, target: Path, settings: dict[str, str]) -> None:
    before = _read_tags(staged)
    _modify_tags(staged, {f"{KEY_PREFIX}{name}": value for name, value in settings.items()})
    _require_foreign_tags(before, _read_tags(staged), target)


def _read_tags(path: Path) -> dict[str, str]:
    pyexiv2.registerNs(NAMESPACE_URI, NAMESPACE_PREFIX)
    image = pyexiv2.Image(str(path))
    try:
        return dict(image.read_xmp())
    finally:
        image.close()


def _modify_tags(path: Path, tags: dict[str, str]) -> None:
    image = pyexiv2.Image(str(path))
    try:
        image.modify_xmp(tags)
    finally:
        image.close()


def _require_foreign_tags(before: dict[str, str], after: dict[str, str], target: Path) -> None:
    lost = sorted(key for key in before if _is_foreign(key) and key not in after)
    if lost:
        raise SidecarError(f"Sidecar write would drop {lost} in {target}")


def _is_foreign(key: str) -> bool:
    return not key.startswith(KEY_PREFIX)


def _develop_keys(tags: dict[str, str]) -> dict[str, str]:
    return {key[len(KEY_PREFIX):]: value for key, value in tags.items() if key.startswith(KEY_PREFIX)}
