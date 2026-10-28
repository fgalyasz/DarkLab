---
title: DarkLab cull marks survive restart
status: final
created: 2026-10-28
updated: 2026-10-28
extends: prd-DarkLab-2026-10-10
parent_issue: 7
story_issue: 10
---

# PRD: Cull marks survive restart

## 0. Document Purpose

This PRD adds FR-61. Rating, Flag, and Color Label set in Library are stored in the Catalog, show again after a restart, and show on the same Photo in Develop. It builds on FR-14.

## 1. Vision

A Photographer culls a shoot, quits, and finds every star, flag, and color where it was left.

## 2. Features

### 2.1 Marks in the Catalog

**Description:** Each Photo row keeps a Rating (0 to 5), a Flag (none, accepted, rejected), and a Color Label (none, red, orange, yellow, green, blue, purple).

#### FR-61: Rating, Flag, and Color Label persist per Photo

**Consequences (testable):**
- Setting a Rating, Flag, or Color Label in the Library grid writes it to that Photo in the Catalog.
- Opening the Catalog shows the stored marks on the grid. A Photo with no stored marks shows no stars, no flag, and no color.
- Develop shows the stored marks of the Photo it displays.
- A value outside the allowed set is rejected and nothing is stored.
- Removing a Photo from the Catalog removes its marks with it.
- The Original file and its content hash are unchanged.

## 3. Non-Goals

- Filtering by Flag and Color Label (story 2.4).
- Editing marks inside Develop.
- Writing marks to an XMP sidecar.

## 4. Open Questions

None for this change.
