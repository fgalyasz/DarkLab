---
title: DarkLab import mode grouping
status: final
created: 2026-10-11
updated: 2026-10-11
extends: prd-DarkLab-2026-10-10
parent_issue: 1
story_issue: 56
---

# PRD: Import mode grouping

## 0. Document Purpose

This PRD records a layout correction for baseline FR-5. It does not add a new FR id.

## 1. Vision

Copy, Move, and Add are three ways to bring a file into the Catalog. They read as one choice. Assisted Culling is a different mode and does not sit in that choice.

## 2. Features

### 2.1 One method group

**Description:** Implements the presentation of FR-5.

#### FR-5, as presented here

**Consequences (testable):**
- Copy, Move, and Add are one row, in that order.
- Assisted Culling is outside that row.
- The Add caption appears only while Add is selected, and it does not pull Add out of the row.

## 3. Non-Goals

- Changing what Add, Copy, Move, or Assisted Culling do.
- A new import method.

## 4. Open Questions

None for this change.
