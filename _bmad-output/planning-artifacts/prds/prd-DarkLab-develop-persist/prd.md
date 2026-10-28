---
title: DarkLab Develop tone survives restart
status: final
created: 2026-10-28
updated: 2026-10-28
extends: prd-DarkLab-2026-10-10
parent_issue: 75
story_issue: 76
---

# PRD: Develop tone survives restart

## 0. Document Purpose

This PRD adds FR-60. Basic tone changes made in Develop are stored in the Catalog and load again when the Photo is shown. It builds on FR-21 and FR-23.

## 1. Vision

Develop is not a throwaway preview. A Photographer moves a tone slider, quits, reopens the Catalog, and finds the same values on the same Photo.

## 2. Features

### 2.1 Tone Develop Settings in the Catalog

**Description:** The six Tone sliders (Exposure, Contrast, Highlights, Shadows, Whites, Blacks) are saved per Photo in the Catalog's Develop Settings.

#### FR-60: Basic tone is persisted per Photo

**Consequences (testable):**
- Changing a Tone slider for a Photo writes that value to the Photo's Develop Settings in the Catalog.
- Showing the Photo in Develop after a restart sets every Tone slider to its stored value. A Photo with no stored value shows the default.
- Settings that Develop does not edit (for example keys restored from an XMP sidecar) are kept when tone is saved.
- The Original file and its content hash are unchanged.
- A stored value that is not a whole number is ignored and the default is shown.

## 3. Non-Goals

- Persisting sliders other than Tone, crop, or History.
- Writing the XMP sidecar on every change.
- Choosing which Photo Develop shows from Library selection (story 19.2).

## 4. Open Questions

None for this change.
