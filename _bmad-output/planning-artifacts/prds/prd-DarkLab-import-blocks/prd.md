---
title: DarkLab import blocks
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 58
---

# PRD: Import blocks

## 0. Document Purpose

This PRD corrects the Import window. File renaming, metadata editing, and destination presets stay. The window gives each of them a shaded block. It does not add a new FR id.

## 1. Vision

A Photographer can tell the parts of Import apart. Renaming, metadata, and the destination preset are each their own block.

## 2. Features

### 2.1 Shaded blocks

**Description:** Presents FR-5 and the metadata applied during Import.

**Consequences (testable):**
- File Renaming, Metadata, and Destination are three blocks, in that order.
- Each block has its own title bar and a darker body.
- Destination shows the active preset, its folder, Choose Folder, and Configure.
- Choosing a folder updates that preset and leaves the other presets in place.
- The top bar, source column, grid, and bottom bar are separate bands.

## 3. Non-Goals

- Removing renaming, metadata, or destination presets.
- A new metadata field.

## 4. Open Questions

None for this change.
