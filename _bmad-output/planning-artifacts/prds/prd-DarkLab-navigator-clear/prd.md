---
title: DarkLab navigator clears on removal
status: final
created: 2026-10-12
updated: 2026-10-12
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 61
---

# PRD: Navigator clears on removal

## 0. Document Purpose

This PRD records a correction to FR-58. Removing an index image also clears the Navigator. It does not add a new FR id.

## 1. Vision

After an index image leaves the Catalog, the Navigator no longer shows that photograph.

## 2. Features

### 2.1 Empty Navigator

**Description:** Completes the visible half of FR-58.

#### FR-58, as corrected here

**Consequences (testable):**
- Removing the selected index image clears the Navigator pixmap.
- The Navigator then says that no photograph is selected.

## 3. Non-Goals

- A new removal choice.
- Rebuilding a deleted index image.

## 4. Open Questions

None for this change.
