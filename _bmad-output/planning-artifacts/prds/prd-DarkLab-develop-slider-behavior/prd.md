---
title: Develop slider behavior and Basic tone preview
status: final
created: 2026-11-21
updated: 2026-11-21
extends: prd-DarkLab-2026-10-10
parent_issue: https://github.com/fgalyasz/DarkLab/issues/162
---

# PRD: Develop slider behavior and Basic tone preview

## 0. Document Purpose

Photographers expect every Basic / WB / Presence slider to change the Preview (FR-23), double-click to reset a control, and arrow keys (Shift = coarse) once a slider is focused.

## 1. Vision

On Develop, moving Highlights, Shadows, Whites, Blacks, Texture, Clarity, or Dehaze updates the Preview and Export the same way Exposure already does. Double-click restores the control default; arrow keys nudge values.

## 2. Features

#### FR-81: Slider reset and keyboard nudge

**Consequences:**
- Double-click on a `SliderRow` sets its value to the row default.
- With the slider focused, Left/Down decrease and Right/Up increase by 1; Shift+those keys change by 10.
- Clicking the slider focuses it for keyboard input.

#### FR-82: Basic tone zones apply to Preview and Export

**Consequences:**
- Highlights, Shadows, Whites, and Blacks change Preview pixels (not only catalog storage).
- Export uses the same `BasicTone` path.
- All `TONE_KEYS` trigger live Preview refresh (including Texture / Clarity / Dehaze).

## 3. Non-Goals

- Tone Curve, HSL mixer, Detail, Lens, Transform, Effects, Calibration full pipelines (FR-24+ / complete Develop epic).
- Soft Proofing.

## 4. Open Questions

None.
