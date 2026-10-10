---
title: DarkLab import summary
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 3
---

# PRD: Import summary

## 0. Document Purpose

This PRD records the implementation of baseline FR-5 and FR-7 for story 1.2. It does not add a new FR id.

## 1. Vision

Before Import commits, the Photographer sees how many files are selected and how many bytes that selection is. Add, Copy, and Move do what their names say.

## 2. Features

### 2.1 Summary and transfer

**Description:** Implements FR-5 and FR-7. Realizes the import half of UJ-1.

#### FR-5 and FR-7, as implemented here

**Consequences (testable):**
- The summary byte count is the selection, and it changes when the selection changes.
- Commit stays disabled while the selection is empty.
- Copy writes the destination and leaves the source file in place.
- Move removes the source only after the destination exists and the sizes match.
- A failed copy leaves the source in place.
- Add reports how many files have been recorded.
- The folder walk that lists images does not run on the UI thread.

## 3. Non-Goals

- Duplicate detection. That is story 1.3.
- Applying Keywords and Metadata during Import. That stays with FR-16 and FR-17.

## 4. Open Questions

None for this change.
