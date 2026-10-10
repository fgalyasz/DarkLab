---
title: DarkLab import duplicates
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 4
---

# PRD: Skip duplicates

## 0. Document Purpose

This PRD records the implementation of baseline FR-8 for story 1.3. It does not add a new FR id.

## 1. Vision

A second copy of a card does not double the grid. Import skips an Original whose bytes are already in the Catalog, unless the Photographer asks for another Photo.

## 2. Features

### 2.1 Duplicate skip

**Description:** Implements FR-8. Realizes the duplicate half of UJ-1.

#### FR-8, as implemented here

**Consequences (testable):**
- The default action is skip.
- Skip does not create a Photo, does not change the existing Photo, and does not copy or move the file.
- The same path is never a second Photo, even when the Photographer asks to import duplicates.
- A different path with the same bytes becomes a second Photo only when that choice is on.
- Photos imported before the hash column still match, once their files are still on disk.

## 3. Non-Goals

- A per-file prompt. The choice is one checkbox for the commit.
- Marking a missing Original or writing a Sidecar. That is story 1.4.

## 4. Open Questions

None for this change.
