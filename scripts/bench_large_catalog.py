import os
import random
import sqlite3
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtWidgets import QApplication

from src.catalog.database import create_catalog
from src.catalog.locations import database_file
from src.ui.panels.library_browser_panel import LibraryBrowserPanel

APP = QApplication.instance() or QApplication([])
DEFAULT_COUNT = 100_000
OPEN_LIMIT_SECONDS = 2.0
FILTER_LIMIT_SECONDS = 0.2
INSERT = "INSERT INTO photos (id, original_path, rating, pick, capture_time) VALUES (?, ?, ?, ?, ?)"


def build_catalog(count: int) -> Path:
    catalog = create_catalog(Path(tempfile.mkdtemp()) / "bench")
    rows = [_row(number) for number in range(1, count + 1)]
    connection = sqlite3.connect(database_file(catalog))
    with connection:
        connection.executemany(INSERT, rows)
    connection.close()
    return catalog


def _row(number: int) -> tuple[int, str, str, str, float]:
    pick = random.choice(("none", "accepted", "rejected"))
    return number, f"/shoot/{number // 500}/IMG_{number}.jpg", str(random.randint(0, 5)), pick, float(number)


def seconds_of(action: Callable[[], None]) -> float:
    started = time.perf_counter()
    action()
    APP.processEvents()
    return time.perf_counter() - started


def choose(panel: LibraryBrowserPanel, combo_name: str, value: str) -> None:
    combo = getattr(panel, combo_name)
    combo.setCurrentIndex(combo.findData(value))


def report(label: str, seconds: float, limit: float) -> bool:
    verdict = "ok" if seconds <= limit else "SLOW"
    print(f"{label}: {seconds:.2f} s (limit {limit} s) {verdict}")
    return seconds <= limit


def main() -> int:
    random.seed(1)
    count = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_COUNT
    catalog = build_catalog(count)
    panel = LibraryBrowserPanel()
    panel._pool.setMaxThreadCount(0)
    results = [report(f"open {count} photos", seconds_of(lambda: panel.show_catalog(catalog)), OPEN_LIMIT_SECONDS)]
    results.append(report("flag filter", seconds_of(lambda: choose(panel, "pick_combo", "accepted")), FILTER_LIMIT_SECONDS))
    results.append(report("rating filter", seconds_of(lambda: choose(panel, "rating_combo", "4")), FILTER_LIMIT_SECONDS))
    panel._cancel_load()
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
