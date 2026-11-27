---
title: Classic Darkroom Panel Design
status: final
created: 2026-11-27
updated: 2026-11-27
extends: prd-DarkLab-2026-10-10
supersedes_partially: prd-DarkLab-uniform-panels
parent_issue: https://github.com/fgalyasz/DarkLab/issues/164
---

# PRD: Classic Darkroom Panel Design

## 0. Document Purpose

Align DarkLab's Library and Develop side panels, sliders, dividers, scrollbars, and chrome with the founder-provided classic darkroom reference: matte charcoal headers, neutral `#505050` panel surfaces, sharp edges, etched bevel dividers, custom upward-pointing pentagon slider pointers with upper tick marks, right-aligned slider labels, and slim dark scrollbars.

## 1. Vision

A Photographer moving between Library and Develop sees a calm, matte, distraction-free darkroom workspace without glossy gradients or rounded card nesting. Every control sits on a uniform neutral-gray panel surface, separated by etched bevel dividers, with precision pentagon slider pointers aligned directly to tick marks.

## 2. Features

#### FR-116: Matte classic panel shell and column alignment

**Consequences (testable):**
- `CollapsibleSection` uses flat matte charcoal headers (`rgb(50, 50, 50)`), neutral gray panel bodies (`rgb(80, 80, 80)`), sharp corners (`Density.PANEL_CORNER_RADIUS_PX == 0`), and `1px` dark outer borders (`rgb(14, 14, 14)`).
- Left-column panels (`Navigator`, `Presets`, `Snapshots`, `History`, `Collections`, `Catalog`, `Folders`, `Publish Services`) render the disclosure triangle on the left with left-aligned titles (`arrow_on_left=True`).
- Right-column panels (`Histogram`, `Basic`, `Tone Curve`, `Color Mixer`, `Color Grading`, `Detail`, `Lens Corrections`, `Transform`, `Effects`, `Calibration`, `Quick Develop`, `Keywording`, `Keyword List`, `Metadata`, `Comments`) render right-aligned titles next to the right-side disclosure triangle (`arrow_on_left=False`).
- Body labels keep at least `4.5:1` WCAG contrast (`NFR-7`) against both `QWidget` (`rgb(50, 50, 50)`) and panel bodies (`rgb(80, 80, 80)`).

#### FR-117: Seamless Develop sub-groups and two-tier etched dividers

**Consequences (testable):**
- `DevelopGroup` renders seamlessly on the `#505050` panel surface without nested card borders or glossy header bars, while preserving click-to-collapse behavior.
- Major sub-groups (`Treatment`, `WB`, `Tone`, `Presence`, etc.) are separated by a full-width 2px etched bevel divider (`1px rgb(24, 24, 24)` over `1px rgb(92, 92, 92)`), omitted on the first group of a panel.
- Sub-group headings (`Tone`, `Presence`, etc.) align horizontally with the slider track start edge.
- Within `Tone` (between `Contrast` and `Highlights`) and `Presence` (between `Dehaze` and `Vibrance`), a subtle soft etched hairline (`1px rgb(70, 70, 70)` over `1px rgb(88, 88, 88)`) separates tonal sub-clusters with balanced vertical breathing space.

#### FR-118: Precision pentagon slider pointer, upper tick marks, and right-aligned rows

**Consequences (testable):**
- `DevelopSlider` custom-paints a recessed horizontal groove, 9 evenly spaced vertical tick marks directly above the groove (taller at left, center, and right), and an upward-pointing pentagon pointer with dark outline and subtle metallic fill (brightening on hover/press).
- `SliderRow` right-aligns captions directly adjacent to the slider track, right-aligns signed numeric readouts (`+` for positive bipolar values, `0` for zero, `+0.00`/`-0.30`/`0.00` for `Exposure`), and keeps fixed single-line row height (`SLIDER_ROW_HEIGHT = 20`) with balanced `8px` horizontal spacing.
- Double-click reset and arrow / Shift+arrow keyboard nudging (`FR-81`) remain intact.

#### FR-119: Matte chrome for tool strip, action bars, scrollbars, module bar, and filmstrip

**Consequences (testable):**
- The Develop tool strip sits in a recessed charcoal band (`rgb(62, 62, 62)`) with flat borderless tool buttons directly below `Histogram`.
- Bottom panel action bars (`Previous` / `Reset`) use equal-width matte beveled buttons separated by a crisp dark seam.
- Scrollbars render as slim `9px` dark tracks (`rgb(16, 16, 16)`) with rounded gray pill handles and no arrow buttons; splitter handles render as crisp `3px` dark seams.
- Tree and list widgets (`Presets`, `History`, `Catalog`, `Folders`, `Collections`) sit seamlessly on the `#505050` panel body without heavy black inset boxes.
- The module bar uses a near-black bar (`rgb(14, 14, 14)`) with subtle vertical separators; the filmstrip uses a neutral charcoal trough (`rgb(44, 44, 44)`) with a classic light-gray active cell frame (`rgb(190, 190, 190)`).

## 3. Non-Goals

- Adding new image-processing pipelines (Tone Curve / HSL / Detail stay in Epic #163).
- Adding vectorscope or HDR toggle behavior.
- Changing catalog schema, keyboard shortcuts, or non-destructive Develop persistence.

## 4. Open Questions

None.
