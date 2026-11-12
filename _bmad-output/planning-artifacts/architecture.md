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

Import, whether Add, Copy, or Move, records each resulting file in the open Catalog and writes `previews/{photo_id}.jpg`. Each Photo stores a SHA-256 `content_hash` of the Original. Import skips a file whose hash is already stored, unless the Photographer asks for a second Photo. Skip does not write a new Photo, does not change the stored hash, and does not copy or move the file. Copy leaves the source in place. Move removes the source only after the destination file exists and its size matches. A legacy single-file Catalog stores that cache in a sibling folder named `<file>.previews`. The folder walk lives in `src/importing` and runs off the UI thread. `src/importing` does not import Qt.

### ADR-3 — Originals are read-only

No DarkLab code path opens an Original for write. Export and preview write only under the export destination or the Catalog's `previews/` directory. Tests for FR-21 and FR-37 hash the Original before and after.

Move-import may delete a source only after the destination file exists and its size matches (FR-5). That deletes the source path the Photographer chose to move. Removing a Photo from the Catalog deletes its index image and its Photo row. The Original file is deleted only when the Photographer chooses that in the removal dialog (FR-58), and only that stored path.

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

### ADR-10 — Configurable Auto-Cull engine (`src/culling`)

Per-Photo quality metrics (`sharpness_score`, `face_count`, `eyes_open_score`, `all_eyes_open`, `smile_score`, `exposure_score`, `framing_score`, `perceptual_hash`) are extracted off the UI thread in `src/culling/metrics.py` and cached in `catalog.sqlite` (`photo_cull_metrics` table keyed by `photo_id` and `content_hash`). `src/culling/scorer.py` and `src/culling/burst.py` evaluate `CullCriteria` weights, burst windows, and hard defect triggers synchronously from cached metrics so changing slider weights in the UI re-ranks 500+ Photos in <50 ms without re-decoding Originals.

### ADR-11 — Complete 12-stage unified Develop pipeline (`src/imaging/pipeline.py`)

Every control in `DevelopPanel` maps to a canonical key in `src/develop/settings_schema.py` and is rendered through `src/imaging/pipeline.py` in a single fixed 12-stage order shared by Preview and Export:
1. Calibration primaries (`src/imaging/effects_calibration.py`)
2. Lens profile & chromatic aberration (`src/imaging/lens_transform.py`)
3. Perspective Transform + Constrain Crop + Straighten & Crop (`src/imaging/lens_transform.py`, `src/imaging/crop.py`)
4. Spot Heal/Clone & Red Eye (`src/imaging/healing.py`, `src/imaging/red_eye.py`)
5. White Balance & Color/B&W Treatment (`src/imaging/color_grade.py`, `src/imaging/treatment.py`)
6. Basic Tone & Presence (`src/imaging/tone.py`, `src/imaging/presence.py`)
7. Parametric & Point Tone Curves (`src/imaging/tone_curve.py`)
8. 8-Band HSL / B&W Color Mixer (`src/imaging/hsl_mixer.py`)
9. 4-Way Color Grading Wheels (`src/imaging/color_wheels.py`)
10. Regional Local Masks (`src/imaging/masking.py`)
11. Detail: AI/Wavelet Noise Reduction & Edge-Masked Sharpening (`src/imaging/detail.py`, `src/ai/denoise_sharpen.py`)
12. Post-Crop Vignetting & Deterministic Film Grain (`src/imaging/effects_calibration.py`)

`photo_history` and `photo_snapshots` tables in `catalog.sqlite` persist History Steps and named Snapshots per Photo across restarts.

### ADR-12 — Deterministic Auto-Corrections write editable Develop Settings

`src/develop/auto_tone.py`, `src/develop/auto_wb.py`, `src/develop/auto_upright.py`, and `src/develop/auto_lens.py` analyze pixel histograms, neutral illuminant ratios, Hough/LSD line segments, and EXIF lens tags, and return standard `develop_settings` dictionaries (`Exposure`, `Highlights`, `Shadows`, `Whites`, `Blacks`, `Temp`, `Tint`, `CropAngle`, `TransformVertical`, `RemoveCA`, etc.) rather than baking opaque pixel filters.

### ADR-13 — Local-first AI Corrections & Semantic Masks (`src/ai`)

All AI correction features (`src/ai/semantic_masks.py`, `src/ai/scene_corrector.py`, `src/ai/portrait_retouch.py`, `src/ai/denoise_sharpen.py`, `src/ai/spot_detector.py`, `src/ai/adaptive_presets.py`) execute locally without network sockets (`ADR-8`), leave Originals untouched (`ADR-3`), and output editable `develop_settings`, semantic `Masks`, or `HealStrokes`. `src/ai/model_registry.py` provides a two-tier local execution backend (local ONNX/DNN weights when present, with a deterministic multi-scale CV/frequency/saliency engine built in so all features run offline on macOS, Windows, Linux, and CI).

### ADR-14 — Configurable Auto-Crop separates anchor detection from 2D geometry solving

`src/develop/auto_crop_anchors.py` detects faces, eye-lines, group bounding boxes, visual saliency centroids, and horizon tilt angles. `src/develop/auto_crop_solver.py` is a pure deterministic geometry function that computes the largest inscribed rotated rectangle (`CropAngle`), enforces group-face safety (`never_cut_faces`), fits the requested `aspect_ratio`, aligns the focal anchor to the chosen `composition_rule` (`rule_of_thirds`, `golden_ratio`, `center_subject`, `portrait_headroom`, `horizon_thirds`), and returns `CropSettings`.

### ADR-15 — Multi-Photo Batch Engine distinguishes static Sync from per-photo computed Batch

`src/develop/sync_groups.py` copies selected parameter groups from the Primary Photo to Secondary selected Photos (`Sync...` and live `Auto-Sync`). `src/develop/batch_adjust.py` applies relative (`Δ`) or absolute adjustments and `Match Total Exposure`. `src/develop/batch_processor.py` runs computed operations (Batch Auto Tone, Auto WB, Auto Upright, Configurable Auto-Crop, and AI Corrections) independently on each selected Photo's own pixels off the UI thread, writing one atomic transaction + History Step per Photo.

### ADR-16 — Model Tier & Cost-Effective Implementation Architecture

- **Frontier Planning Model for PRDs, Architecture, and Documentation:** All PRDs, architecture revisions, epic/story definitions, and technical specifications must be authored with the best available frontier reasoning/planning model to ensure exhaustive edge-case coverage and zero architectural ambiguity.
- **Cost-Effective Model Optimization for Development:** Every Story ticket must include a **Cost-Effective Implementation Blueprint** naming exact target files, function signatures (≤10 lines per function), settings/SQLite keys, and deterministic unit test files (`>=95%` coverage) so cost-effective coding models (`Composer 2.5 Fast`) can implement each story in a single pass.

## Structure

```text
src/catalog/        SQLite, photos, folders, sidecar IO, cull metrics, history & snapshots
src/culling/        configurable auto-cull criteria, quality metrics, burst grouping, scorer
src/importing/      add, copy, move, duplicate hash, summary
src/develop/        settings schema, history, presets, auto-tone/wb/upright/lens, auto-crop, sync & batch
src/ai/             local-first semantic masks, scene auto-develop, portrait retouch, denoise, spot heal
src/exporting/      render-to-file, export presets
src/imaging/        decode and the single 12-stage render pipeline
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
