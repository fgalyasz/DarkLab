---
title: DarkLab filter the cull
status: final
created: 2026-10-29
updated: 2026-10-29
extends: prd-DarkLab-2026-10-10
parent_issue: 7
story_issue: 11
---

# PRD: Filter the cull

## 0. Document Purpose

This PRD delivers the first-milestone part of FR-15 (Filter) and the contrast check of NFR-7. Library can narrow the grid by text, Rating, Flag, and Color Label, and clearing the filter brings back the whole source.

## 1. Vision

A Photographer sets a Flag or a Color Label while culling, then filters to exactly those Photos and delivers that set.

## 2. Features

### 2.1 Library filter

**Description:** The Library filter bar combines filename text, a minimum Rating, a Flag choice (Picked, Rejected, Unflagged), and a Color Label choice (a color or none). A Clear button resets every control.

#### FR-62: Filter by Flag and Color Label

**Consequences (testable):**
- Choosing Picked shows only Photos whose Flag is accepted, and the grid count equals the Pick count in the source.
- Choosing a Color Label shows only Photos with that label. Unflagged and No color match Photos with nothing set.
- Text, Rating, Flag, and Color Label combine: a Photo must satisfy all of them.
- Clear, or setting every control back to Any, shows the full source count.
- Filtering never changes a mark, a Develop Setting, or an Original.

### 2.2 Dark theme contrast

#### FR-63: Body labels meet 4.5:1

**Consequences (testable):**
- Body label text on the Library dark theme has a contrast ratio of at least 4.5:1 against its background.
- A test computes the ratio from the theme stylesheet, so a later theme edit that drops below 4.5:1 fails.

## 3. Non-Goals

- Filtering by Keyword or capture date (FR-16, FR-17).
- Saving a filter as a Smart Collection (FR-13).
- Multi-value filters (for example two colors at once).

## 4. Open Questions

None for this change.
