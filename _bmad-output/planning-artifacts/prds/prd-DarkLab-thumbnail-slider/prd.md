---
title: DarkLab thumbnail slider matches the grid
status: final
created: 2026-10-12
updated: 2026-10-12
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 62
---

# PRD: Thumbnail slider matches the grid

## 0. Document Purpose

This PRD adds FR-59. The Library Thumbnails slider and the index images agree when the Library opens. It extends the baseline and the Library grid PRD.

## 1. Vision

The index images open at the size the Thumbnails slider is already showing.

## 2. Features

### 2.1 Startup size

**Description:** The grid uses the slider position and the width of the view that is actually on screen.

#### FR-59: Index image size follows the slider

**Consequences (testable):**
- When the Library opens, the index image size is the size selected by the current Thumbnails slider position.
- Moving the slider changes the index image size to the new position.

## 3. Non-Goals

- Remembering the slider position across launches.
- Changing the filmstrip size.

## 4. Open Questions

None for this change.
