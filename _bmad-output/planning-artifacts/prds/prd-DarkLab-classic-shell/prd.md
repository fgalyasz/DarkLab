---
title: DarkLab Classic shell fidelity
status: final
created: 2026-11-06
updated: 2026-11-06
extends: prd-DarkLab-2026-10-10
parent_issue: 79
story_issues: [80, 81, 82]
---

# PRD: Classic shell fidelity

## 0. Document Purpose

This PRD records the implementation of baseline FR-C1 and FR-C2 for stories 20.1, 20.2, and 20.3. It adds no new FR id. The checklist the stories compare against is in `addendum.md`.

## 1. Vision

A Photographer who knows Lightroom Classic finds the module bar, columns, filmstrip, panel order, and Import bands where they expect them.

## 2. Features

#### FR-C1 and FR-C2, as implemented here

**Consequences (testable):**
- Library shows the filmstrip under the main view, a left column (Navigator, Catalog, Folders, Collections, Publish Services) and a right column (Histogram, Quick Develop, Keywording, Keyword List, Metadata, Comments).
- Develop's right column lists Histogram, then the tool strip, then Basic through Calibration in Classic order. The left column lists Navigator, Presets, Snapshots, History, Collections.
- Import keeps source, grid, and options as three distinct bands. Copy, Move, and Add share one choice row. The options band shows no horizontal scrollbar at the default width.
- Body label contrast stays at or above 4.5:1 (NFR-7) on the Library and Develop panels.
- The checks are automated, so a later change that reorders a panel fails a test.

## 3. Non-Goals

- Pixel-identical Lightroom chrome. DarkLab claims Classic-like structure only.
- Panels whose epic has not shipped. Their sections exist and stay empty or minimal.

## 4. Open Questions

None.
