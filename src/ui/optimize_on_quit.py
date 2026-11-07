from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtWidgets import QWidget

from src.catalog.optimize import CatalogOptimizeError, optimize_catalog
from src.catalog.optimize_policy import OptimizePolicy
from src.ui.progress_reporter import CancellableProgressReporter

logger = logging.getLogger(__name__)

_import_copy_active = False


def set_import_copy_active(active: bool) -> None:
    global _import_copy_active
    _import_copy_active = active


def import_copy_active() -> bool:
    return _import_copy_active


def optimize_on_quit(parent: QWidget, catalog: Path | None, policy: OptimizePolicy) -> bool:
    if catalog is None or not policy.on_quit_enabled or import_copy_active():
        return False
    reporter = CancellableProgressReporter(parent, "Optimize Catalog")
    try:
        optimize_catalog(catalog, reporter, reporter.cancelled)
    except CatalogOptimizeError as error:
        reporter.close()
        logger.warning("On-quit optimize skipped: %s", error)
        return False
    reporter.close()
    return True
