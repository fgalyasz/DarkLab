---
title: DarkLab import index images
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 54
---

# PRD: Import index images

## 0. Document Purpose

This PRD extends the baseline and the Library grid PRD. Import must leave index images in the open Catalog so the grid can show them. FR-57 continues the baseline ids.

## 1. Vision

After Import, the Library grid shows an index image for each imported photograph.

## 2. Target User

### 2.1 Jobs To Be Done

- Import or add photographs and see them in the Library without restarting.

### 2.2 Key User Journeys

- **UJ-11. Anna imports a card.**
  - **Entry state:** A Catalog is open and the Library grid is empty.
  - **Path:** She selects photographs and imports them, or adds them without copying.
  - **Climax:** Closing the Import dialog shows one index image per imported photograph.
  - **Resolution:** Importing the same file again does not add a second Photo.
  - **Edge case:** A file that cannot be read is skipped. The others still appear.

## 3. Features

### 3.1 Import writes index images

**Description:** Add and Copy record the resulting file in the open Catalog and store an index image. Realizes UJ-11.

**Functional Requirements:**

#### FR-57: Import fills the grid

Importing photographs into the open Catalog writes an index image for each one, and the Library lists them when Import closes.

**Consequences (testable):**
- Add records the selected files. Copy records the files written to the destination.
- Each new file gets one Photo row, its folder path, and one index image.
- Importing the same path again does not add a second Photo.
- A missing or unreadable file is skipped.
- A Catalog that is still a single database file stores the index images beside that file.
- The Library grid lists those index images after the Import dialog closes.

## 4. Non-Goals

- Copy, move, and rename options beyond the index image and the Photo row.
- Rebuilding an index image after the preview cache is deleted.

## 5. MVP Scope

FR-57 is in scope for this change.

## 6. Success Metrics

- **SM-7:** Importing two JPEGs into an empty Catalog yields two index images and two Photo rows. Validates FR-57.

## 7. Open Questions

None for this change.

## 8. Assumptions Index

- The file recorded for Copy is the destination file. [ASSUMPTION: the Catalog points at the copy, which is the file DarkLab will open later.]
