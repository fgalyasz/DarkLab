from __future__ import annotations

from pathlib import Path

from src.exporting.batch import ExportReport


def export_blocker(selected: int, renderable: int, folder: Path | None) -> str | None:
    if selected == 0:
        return "Select at least one photo in the Library to export."
    if renderable == 0:
        return "None of the selected photos has its original file, so there is nothing to render."
    if folder is None:
        return "Choose a destination folder."
    return None


def skip_note(selected: int, renderable: int) -> str:
    skipped = selected - renderable
    if skipped <= 0:
        return ""
    return f"{skipped} selected photo(s) have no original and will be skipped."


def report_summary(report: ExportReport) -> str:
    parts = [f"Exported {len(report.written)} photo(s)."]
    if report.missing:
        parts.append("Skipped, original missing: " + ", ".join(path.name for path in report.missing) + ".")
    if report.failed:
        parts.append("Failed: " + "; ".join(f"{path.name} ({reason})" for path, reason in report.failed) + ".")
    return " ".join(parts)
