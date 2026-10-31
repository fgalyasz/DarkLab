---
title: DarkLab Library sort
status: final
created: 2026-10-31
updated: 2026-10-31
extends: prd-DarkLab-2026-10-10
parent_issue: 7
story_issue: 8
---

# PRD: Library sort

## 0. Document Purpose

This PRD adds FR-75. It completes the sort half of story 2.1: the grid sorts by capture time, file name, Import time, and Rating. The Module bar order and the empty Modules already match Classic.

## 1. Vision

The Photographer walks a shoot in the order that fits the pass she is making: as shot, by name, as imported, or best first.

## 2. Features

#### FR-75: Grid sort

The Library sort control offers Capture Time, File Name, Import Time, and Rating. The grid order and the filmstrip follow the choice.

**Consequences (testable):**
- Capture Time orders by the capture date stored in the Original (oldest first). A Photo with no capture date uses the Original's file date, and a Photo whose Original is missing sorts after the others.
- File Name orders by the Original's file name, case-insensitive, A to Z. It is not the name of the index image.
- Import Time orders by the order the Photos entered the Catalog, first imported first.
- Rating orders from five stars down to none.
- Photos that tie keep Import order.
- Filters apply before the sort, and the sort never changes a mark, a setting, or a file.

## 3. Non-Goals

- Descending order toggle.
- Re-sorting the grid the moment a Rating changes. The new Rating counts at the next refresh or sort change.
- Sorting by edit time, aspect ratio, or other fields.

## 4. Open Questions

None.
