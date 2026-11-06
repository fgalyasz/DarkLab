---
title: DarkLab Optimize Catalog
status: final
created: 2026-11-06
updated: 2026-11-06
extends: prd-DarkLab-2026-10-10
parent_issue: 90
story_issue: 94
---

# PRD: Optimize Catalog

## 0. Document Purpose

This PRD records the implementation of baseline FR-R4 for story 22.4. It adds no new FR id.

## 1. Vision

A Catalog that grew over years of imports stays responsive without the Photographer hunting for a maintenance ritual.

## 2. Features

#### FR-R4, as implemented here

File → Optimize Catalog tunes the open Catalog.

**Consequences (testable):**
- Optimize creates the documented indexes for Photo hash, original path (Folder lookups), and cull marks (pick, rating) when they are missing, refreshes query statistics, and compacts free pages.
- The integrity check passes before Optimize starts and again afterwards. A damaged Catalog is refused and left untouched.
- Progress (step label and step count) is shown while Optimize runs.
- Optimize changes no Photo row, mark, Develop Setting, preview, or original.
- A second run creates no index and still passes.

## 3. Non-Goals

- Idle or on-quit Optimize and cancel (story 22.8).
- Large-catalog open and filter performance targets (story 22.5).

## 4. Open Questions

None.
