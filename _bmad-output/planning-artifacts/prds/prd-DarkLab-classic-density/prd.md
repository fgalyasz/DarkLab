---
title: DarkLab Classic density and typography
status: final
created: 2026-11-21
updated: 2026-11-21
extends: prd-DarkLab-2026-10-10
parent_issue: 139
story_issues: [140, 141, 142]
---

# PRD: Classic density and typography

## 0. Document Purpose

Photographers report that DarkLab's chrome feels less dense and less polished than Lightroom Classic: body text is often too large for its slot, labels wrap or clip, and placeholder modules shout with oversized titles. This PRD tightens the shell to Classic-like density without claiming pixel-identical Adobe chrome.

## 1. Vision

A Photographer who knows Lightroom Classic reads DarkLab's module bar, side panels, Develop sliders, Library filter strip, and Import bands at a familiar compact size. Labels fit their rows. Empty modules stay quiet.

## 2. Features

### FR-D1 Compact typography scale

**Consequences (testable):**
- Application body chrome uses an 11px base (`Density.BODY_PX`). Panel headers use 11px. Secondary hints use 10px. No panel title uses a point size above 13.
- `src/ui/density.py` exports `BODY_PX`, `HEADER_PX`, `HINT_PX`, `TITLE_PX`, `MODULE_BAR_HEIGHT`, `PANEL_HEADER_HEIGHT` as the single scale.
- Unit tests assert those constants stay at or below the Classic caps in `addendum.md`.

### FR-D2 Labels fit their slots

**Consequences (testable):**
- Develop `SliderRow` captions use a fixed caption column, single-line elide, and a compact value column so Exposure / Highlights / Saturation stay on one row inside a 280px panel.
- Library Metadata value labels elide in the middle instead of wrapping into a second line.
- Color grading wheels shrink so three wheels fit inside the default Develop right column without a horizontal scrollbar.
- Module placeholder panels no longer use 24pt titles; they use `TITLE_PX` and `BODY_PX`.

### FR-D3 Classic chrome density

**Consequences (testable):**
- Module bar height is `MODULE_BAR_HEIGHT` (30px). Collapsible panel headers are `PANEL_HEADER_HEIGHT` (22px).
- Library filter strip and bottom tool strip use the compact heights in `addendum.md`.
- Global Lightroom stylesheet keeps 2px corner radius and 11px controls; oversized toolbar padding (8×16) is removed from shared button styles.
- Body label contrast on Library and Develop stays at or above 4.5:1 (NFR-7).

## 3. Non-Goals

- Pixel-identical Lightroom chrome or Adobe icons.
- Rewriting Import domain logic or Develop imaging.
- Large iOS-style corner radii; Classic stays near-square (2px).

## 4. Open Questions

None. Founder asked for a full UI pass toward Classic density.
