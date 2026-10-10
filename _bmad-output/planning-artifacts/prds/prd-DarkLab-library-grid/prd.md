---
title: DarkLab library grid
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 52
---

# PRD: Library grid

## 0. Document Purpose

This PRD extends the baseline DarkLab PRD. It specifies what the Library grid shows before Import writes Photos. FR-55 and FR-56 continue the baseline ids.

## 1. Vision

A new Catalog should look empty. The Library grid is the open Catalog's index images, so a Catalog with none of them shows no photographs.

## 2. Target User

### 2.1 Jobs To Be Done

- Create a Catalog and see an empty Library.
- Trust that photographs on disk do not appear until they are in this Catalog.

### 2.2 Key User Journeys

- **UJ-10. Anna creates a Catalog for a new shoot.**
  - **Entry state:** Other photographs already exist on the disk, and an older Catalog may have been open.
  - **Path:** She creates a new Catalog.
  - **Climax:** The Library grid and filmstrip are empty.
  - **Resolution:** She can import later. Until index images exist, the grid stays empty.
  - **Edge case:** Switching back to a Catalog that has index images shows those images, and switching away clears them.

## 3. Features

### 3.1 Library grid

**Description:** The grid lists index images stored in the open Catalog. Realizes UJ-10.

**Functional Requirements:**

#### FR-55: An empty Catalog shows no Photos

A new Catalog opens with an empty Library. Photographs that are only on disk do not appear.

**Consequences (testable):**
- Creating a Catalog does not copy Photos into it.
- Opening that Catalog leaves the Library grid and filmstrip empty.
- A folder on disk that contains photographs does not fill the grid while the Catalog has no index images.

#### FR-56: The grid lists index images

The Library grid is built from the open Catalog's index images.

**Consequences (testable):**
- Index images appear in Photo id order.
- A file in the preview cache that is not an index image is omitted.
- Switching to a Catalog with no index images clears the grid.
- A Catalog saved as a single database file, with no preview cache, shows an empty grid.

## 4. Non-Goals

- Importing photographs in this change. Import still does not write index images.
- Rebuilding missing index images from Originals.

## 5. MVP Scope

FR-55 and FR-56 are in scope for this change.

## 6. Success Metrics

- **SM-6:** A new Catalog shows an empty grid, and a Catalog with two index images shows those two files in id order. Validates FR-55 and FR-56.

## 7. Open Questions

None for this change.

## 8. Assumptions Index

- "Imported images" in the Library means index images stored in the open Catalog. [ASSUMPTION: the grid does not read the application config or scan the disk.]
