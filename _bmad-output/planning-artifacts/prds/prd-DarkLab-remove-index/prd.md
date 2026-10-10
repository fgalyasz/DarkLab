---
title: DarkLab remove index images
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 60
---

# PRD: Remove index images

## 0. Document Purpose

This PRD adds FR-58. A Photographer can remove an index image from the Catalog and choose whether the Original file stays on disk.

## 1. Vision

The Library grid is the Catalog's index images. Removing one asks what should leave: the index image only, or the Original file as well.

## 2. Features

### 2.1 Removal choice

**Description:** Removes a Photo's index image from the open Catalog. Realizes the grid half of UJ-2.

#### FR-58: Remove an index image

The Photographer can remove selected index images from the Catalog. DarkLab asks whether to delete only the index image or also the Original file from disk.

**Consequences (testable):**
- Both choices remove the index image and the Photo row, so the grid no longer lists it.
- Delete index image only leaves the Original file on disk.
- Also delete the original removes that stored file.
- A failed delete of the Original leaves the Photo and its index image in place.
- Cancel removes nothing.

## 3. Non-Goals

- Deleting a file that is not the stored Original path.
- Removing a Photo from a Collection. That stays FR-12.

## 4. Open Questions

None for this change.
