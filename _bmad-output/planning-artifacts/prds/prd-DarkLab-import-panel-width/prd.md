---
title: DarkLab import panel width
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 59
---

# PRD: Import panel width

## 0. Document Purpose

The Import side panel was wider than its column, so its contents opened a horizontal scrollbar. This PRD records that correction. It does not add a new FR id.

## 1. Vision

File Renaming, Metadata, and Destination stay inside the side column. A long name wraps. It does not push the panel sideways.

## 2. Features

### 2.1 Fit the column

**Consequences (testable):**
- At the Import window's default size, the side panel has no horizontal scrollbar.
- The settings content's minimum width is no greater than the side column.

## 3. Non-Goals

- Removing renaming, metadata, or destination presets.
- Changing the height of the window.

## 4. Open Questions

None for this change.
