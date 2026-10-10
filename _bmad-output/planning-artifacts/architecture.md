---
stepsCompleted:
  - step-01-init
  - step-02-context
  - step-03-starter
  - step-04-decisions
  - step-05-patterns
  - step-06-structure
  - step-07-validation
inputDocuments:
  - _bmad-output/planning-artifacts/briefs/brief-DarkLab-2026-10-10/brief.md
  - _bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/prd.md
  - _bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/addendum.md
workflowType: architecture
project_name: DarkLab
user_name: Ferenc
date: 2026-10-10
status: final
---

# Architecture Decision Document

Fast path, 2026-10-10. The step menus were collapsed because the baseline was requested as one pass. Decisions below are binding for implementation unless this file changes.

## Context

DarkLab is a local desktop catalog. Requirements are the PRD. The committed application is a PyQt6 shell: import dialog, library grid, and placeholder panels. It is the starter. It is not the domain model.

The quality bar that drives structure: Originals are immutable (FR-21, FR-37), Develop Settings round-trip (FR-4, SM-2), and the UI thread stays responsive on import (NFR-2).

## Starter

Keep the existing application entry (`main.py`, `src/ui`). Do not generate a new UI project. First structural change is additive packages, not a rewrite.

## Decisions

### ADR-1 — Python and PyQt6 stay

The UI toolkit is PyQt6. The language is Python 3.12 or newer. A native imaging library may be called from `src/imaging`. It does not become a second UI.

Rejected: a Rust or C++ rewrite before a Catalog exists. Recorded in the PRD addendum.

### ADR-2 — One folder is the Catalog

The Photographer picks a `.darklab` folder:

```text
Name.darklab/
  catalog.sqlite
  previews/
  settings.json
```

`catalog.sqlite` holds Photos, imported folder paths, and, as those stories land, Collections, Keywords, History Steps, and Develop Settings. `previews/` holds index images and is disposable. `settings.json` holds settings that belong to that Catalog. Startup Mode, the recent path, and the pin stay in the application config (ADR-9): they are needed before a Catalog is open.

A Catalog created as a single `.darklab` file before this decision still opens. New Catalogs are folders. Open does not rewrite the old file into a folder.

WAL mode is on. The UI opens one connection. Writes go through `src/catalog`. Widgets do not import `sqlite3`.

The Library grid and the Develop filmstrip list index images from the open Catalog. An empty `previews/` directory leaves both empty. They do not scan a disk folder or the application config for Photos.

Import, whether Add or Copy, records each resulting file in the open Catalog and writes `previews/{photo_id}.jpg`. A legacy single-file Catalog stores that cache in a sibling folder named `<file>.previews`. `src/importing` does not import Qt.

### ADR-3 — Originals are read-only

No DarkLab code path opens an Original for write. Export and preview write only under the export destination or the Catalog's `previews/` directory. Tests for FR-21 and FR-37 hash the Original before and after.

Move-import may delete a source only after the destination file exists and its size matches (FR-5). That is the one intentional delete, and it deletes the source path the Photographer chose to move, not a file that was already a Catalog Original elsewhere.

### ADR-4 — XMP sidecar beside the Original

See the addendum. `src/catalog` owns sidecar read and write. A write that drops an unrelated tag is a failed write: leave the previous sidecar in place and surface the error.

### ADR-5 — One render order

`src/imaging` applies Develop Settings in the order fixed in the addendum. Develop preview and Export call that order. A second, UI-only approximation is not allowed for tone, crop, or white balance. The fit-to-screen view may be a downscaled result of that same pipeline (NFR-1), not a different formula.

### ADR-6 — Work leaves the UI thread

Import copies and preview renders run off the UI thread. The widget receives progress counts. Domain functions stay synchronous and free of Qt so tests can call them directly. The Qt adapter owns the thread boundary.

### ADR-7 — The 1920×1080 exit goes away

`main.py` must open on a smaller display. The minimum window size may stay near 1000×700, which the shell already uses. A warning dialog is allowed. `sys.exit` on screen size is not.

### ADR-8 — No network on the shoot path

Import, Library, Develop, and Export do not open sockets. Map is the exception and must tolerate failure.

### ADR-9 — Startup policy stays out of the widget

`src/catalog/startup_policy.py` chooses ask, recent, or fixed. The Catalog Settings dialog collects the choice and does not decide what launch should do. Config keys are `catalog.startup_mode`, `catalog.path`, and `catalog.fixed_path`. A missing recent Catalog and a missing pinned Catalog both show Select Catalog before the workspace. Quit exits. Recent mode with a file still opens that file without asking. Opening a Catalog updates `catalog.path` only.

## Patterns

- A widget calls a service in `src/catalog`, `src/importing`, `src/develop`, or `src/exporting`.
- A service returns data or raises a typed error. It does not import PyQt6.
- `src/imaging` accepts an Original path plus Develop Settings and returns pixels or a preview file. It does not know about Collections or the Module bar.
- Identifiers in code use the glossary: `catalog`, `photo`, `original`, `develop_settings`, `sidecar`. Do not introduce `image` as a synonym for Photo in new modules. The existing `src/ui` names can stay until a file is otherwise edited.
- New functions: type hints, at most ten lines, no nested functions, no docstrings.
- Errors that stop an Import or Export include the path and the operation. Missing files are an expected result, not a traceback on the console as the only signal.
- Logs: info for Import start and finish, Export start and finish, Catalog open. Debug for per-file steps. Warning for a skipped missing Original. Error when the Catalog cannot be saved.

## Structure

```text
src/catalog/        SQLite, photos, folders, sidecar IO
src/importing/      add, copy, move, duplicate hash, summary
src/develop/        settings model, history, presets
src/exporting/      render-to-file, export presets
src/imaging/        decode and the single render order
src/ui/             windows, dialogs, widgets
tests/              unittest, no network, no display for domain tests
```

UI tests that need Qt keep using `QT_QPA_PLATFORM=offscreen`, as the local shell tests already do. Domain tests do not construct a `QApplication`.

Dependency direction: `src/ui` → services → `src/catalog` and `src/imaging`. Services do not import `src/ui`. `src/imaging` does not import `src/catalog`.

## Validation

- FR-1 through FR-8, FR-21, and FR-37 have a home: catalog, importing, develop, exporting.
- NFR-8 applies to those packages, not to every Qt widget.
- The placeholder panels are not evidence that Map, Book, Print, Slideshow, or Web are done.
- CI, when added, runs `python -m unittest discover -s tests` on macOS. The first domain epic adds that workflow. This document does not add CI by itself.
