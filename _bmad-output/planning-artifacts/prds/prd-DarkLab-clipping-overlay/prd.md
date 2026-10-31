---
title: DarkLab clipping overlay
status: final
created: 2026-10-31
updated: 2026-10-31
extends: prd-DarkLab-2026-10-10
parent_issue: 12
story_issue: 16
---

# PRD: Clipping overlay

## 0. Document Purpose

This PRD adds FR-72. It realizes the clipping half of FR-34. The histogram of the current Preview already ships in Develop and Library.

## 1. Vision

The Photographer sees blocked shadows and blown highlights on the Preview before Export, and turns the view off without having changed the photograph.

## 2. Features

#### FR-72: Clipping overlay

A Clipping toggle in the Develop toolbar paints the clipped parts of the Preview. Pixels with a channel at the top of the range are painted red. Pixels with a channel at the bottom of the range are painted blue. A pixel that is both is painted red.

**Consequences (testable):**
- With the toggle on, the Preview shows the overlay for the current settings, including after an exposure or contrast change.
- Turning the toggle off shows the Preview without the overlay.
- Toggling writes no History Step and no Develop Settings, and moves no control.
- The histogram is computed from the Preview without the overlay, so it is the same with the toggle on or off.
- The toggle stays on while the Photographer moves between Photos, is not stored, and starts off in a new session.
- The Original and its content hash are unchanged.

## 3. Non-Goals

- Per-channel clipping colors and adjustable clipping thresholds.
- Clicking histogram corners to switch the overlay.
- A clipping overlay in Library loupe or Export.

## 4. Open Questions

None.
