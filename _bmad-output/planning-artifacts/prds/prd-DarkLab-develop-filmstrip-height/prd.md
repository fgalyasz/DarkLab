---
title: Develop filmstrip thumbnails fully visible
status: final
created: 2026-11-21
updated: 2026-11-21
extends: prd-DarkLab-2026-10-10
parent_issue: https://github.com/fgalyasz/DarkLab/issues/159
---

# PRD: Develop filmstrip thumbnails fully visible

## 0. Document Purpose

Fix the Develop (and shared Library) filmstrip where thumbnail icons were crushed to a thin horizontal strip because IconMode also drew the filename under each icon inside a short cell.

## 1. Vision

A Photographer on Develop sees a full-height filmstrip of readable thumbnails and can click another photograph without guessing from a few pixels of color.

## 2. Features

#### FR-78: Filmstrip shows icon-only thumbnails at usable height

**Consequences (testable):**
- `FilmstripModel` does not expose a DisplayRole filename under the icon; `ToolTipRole` still returns the file name for hover.
- `FilmstripWidget` uses cell/icon sizes tall enough that a set thumbnail’s rendered height is at least 56 px inside the viewport.
- Unit tests cover empty DisplayRole, tooltip name, and minimum icon/cell/widget heights.

## 3. Non-Goals

- Filmstrip scrubbing, ratings badges, or flag overlays.
- Changing windowed thumbnail loading / cache limits.

## 4. Open Questions

None.
