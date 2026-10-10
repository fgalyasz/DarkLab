---
title: DarkLab usable import window
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 57
---

# PRD: A usable Import window

## 0. Document Purpose

This PRD records a layout correction for baseline FR-5. It does not add a new FR id. Renaming, metadata, and develop settings applied during Import stay specified and come later.

## 1. Vision

Import shows the files and the one choice that changes what happens to them. Copy and Move ask for a destination folder. Add does not.

## 2. Features

### 2.1 One side panel

**Description:** Implements the presentation of FR-5.

#### FR-5, as presented here

**Consequences (testable):**
- Copy and Move show a destination folder and a Choose Folder button.
- The chosen folder receives the files in that folder, not in a date tree.
- Add hides the destination panel.
- The bottom bar does not contain an import-preset manager, and Done is not a second close button.

## 3. Non-Goals

- Deleting the unused preset, rename, and metadata code in this change.
- Keywords, sidecars, or develop settings applied during Import.

## 4. Open Questions

None for this change.
