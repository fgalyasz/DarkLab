from __future__ import annotations

import logging
from pathlib import Path

from src.catalog.full_previews import discard_stale_full_previews
from src.catalog.preview_policy import read_preview_policy

logger = logging.getLogger(__name__)


def maintain_preview_cache(catalog: Path) -> int:
    policy = read_preview_policy(catalog)
    removed = discard_stale_full_previews(catalog, policy)
    if removed:
        logger.info("Discarded %s stale 1:1 preview file(s) in %s", removed, catalog)
    return removed
