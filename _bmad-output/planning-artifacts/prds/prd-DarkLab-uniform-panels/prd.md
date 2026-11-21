---
title: Uniform collapsible rounded panels
status: final
created: 2026-11-21
updated: 2026-11-21
extends: prd-DarkLab-2026-10-10
parent_issue: https://github.com/fgalyasz/DarkLab/issues/161
---

# PRD: Uniform collapsible rounded panels

## 0. Document Purpose

Library and Develop side panels must share one chrome: collapsible, rounded corners, and no nested group with the same title as its outer panel (e.g. Crop » Crop).

## 1. Vision

A Photographer sees one consistent panel language everywhere: every side panel collapses, uses the TenPrint/Lightroom-classic rounded shell, and never stacks identical titles.

## 2. Features

#### FR-79: Shared rounded collapsible panel chrome

**Consequences (testable):**
- `CollapsibleSection` uses `Density.PANEL_CORNER_RADIUS_PX` on the shell and header (expanded: top radii; collapsed: full radius), matching `DevelopGroup`.
- `PanelColumn` and the Develop tool stack leave a small gap between rounded sections.
- Theme `#panelHeader` no longer forces `border-radius: 0px`.

#### FR-80: No same-title nested panel

**Consequences (testable):**
- `crop_panel` does not wrap controls in `DevelopGroup("Crop")` because the outer section is already titled Crop.
- A DevelopPanel test asserts no `DevelopGroup` title equals its enclosing `CollapsibleSection` title.

## 3. Non-Goals

- Redesigning slider density or module bar.
- Renaming inner groups that already differ (e.g. WB under Basic).

## 4. Open Questions

None.
