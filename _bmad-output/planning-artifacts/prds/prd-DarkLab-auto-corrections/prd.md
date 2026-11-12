---
title: DarkLab Automatic Image Corrections
status: final
created: 2026-11-11
updated: 2026-11-11
extends: prd-DarkLab-2026-10-10
epic: 25
parent_issue: 117
story_issues: [118, 119, 120, 121]
---

# PRD: Automatic Image Corrections

## 0. Document Purpose

This PRD adds FR-94 through FR-98. It defines fast, deterministic, offline automatic image corrections: **Auto Tone**, **Auto White Balance**, **Auto Presence/Contrast**, **Auto Lens & Chromatic Aberration Correction**, and **Auto Upright / Horizon Leveling** (integrating Epic 21), accessible as one-click actions in Develop, in Library Quick Develop, and optionally on Import.

## 1. Vision

A Photographer wants a reliable one-click starting point that balances exposure, recovers clipped highlights, opens blocked shadows, neutralizes color casts, corrects lens distortion/fringing, and levels a tilted horizon — all by writing editable Develop Settings sliders rather than baking an opaque filter. After clicking `Auto`, every slider shows the exact numeric adjustment DarkLab chose so the Photographer can fine-tune any parameter immediately.

## 2. Features

### 2.1 Deterministic Auto Tone, Auto White Balance, and Auto Presence

#### FR-94: Scene-analyzed Auto Tone (`Exposure`, `Contrast`, `Highlights`, `Shadows`, `Whites`, `Blacks`)

Clicking `Auto` in the Develop Basic panel (or `Auto Tone` in Library Quick Develop) analyzes the Photo's luminance and per-channel histograms and computes optimal values for `Exposure`, `Contrast`, `Highlights`, `Shadows`, `Whites`, and `Blacks`.

**Consequences (testable):**
- Under-exposed images (median luma below target zone) receive a positive `Exposure` and `Shadows` lift; over-exposed images receive negative `Exposure` and `Highlights` recovery.
- `Whites` and `Blacks` stretch the 99.5th and 0.5th percentiles to the full dynamic range without introducing >0.1% new hard clipping.
- The computed values update the sliders, persist to `develop_settings`, and record a single `"Auto Tone"` History Step.
- Original files and hashes remain unchanged.

#### FR-95: Auto White Balance (`Temp` and `Tint`)

Selecting `Auto` in the White Balance dropdown (or running full `Auto Correction`) estimates scene illuminant from neutral/near-neutral midtone pixels (robust gray-world / bright-neutral specular analysis) and sets concrete `Temp` (`2000..50000`) and `Tint` (`-150..150`) values.

**Consequences (testable):**
- A warm indoor tungsten cast reduces `Temp` toward neutral; a cool shade cast increases `Temp`; a green/magenta cast adjusts `Tint`.
- The computed `Temp` and `Tint` values are written to `develop_settings` and remain directly editable via the sliders.

#### FR-96: Auto Presence (`Vibrance`, `Clarity`, `Dehaze`)

When enabled in Auto-Correction preferences, Auto Tone also computes conservative `Vibrance`, `Clarity`, and `Dehaze` values from scene saturation distribution and atmospheric haze floor (dark-channel prior estimate).

**Consequences (testable):**
- Low-contrast hazy frames receive a positive `Dehaze` and `Clarity` boost; already high-saturation portrait skin tones are protected from oversaturation.
- Turning off `Include Presence in Auto Tone` leaves `Texture`, `Clarity`, `Dehaze`, `Vibrance`, and `Saturation` untouched when `Auto` is clicked.

### 2.2 Auto Lens, Chromatic Aberration, and Auto Upright Geometry

#### FR-97: Auto Lens Profile & Chromatic Aberration Correction

DarkLab reads EXIF camera make, model, lens model, focal length, and aperture, matches them against the Lensfun database (when available), and automatically computes lateral Chromatic Aberration alignment (`RemoveCA = "1"`) and peripheral vignetting/distortion parameters.

**Consequences (testable):**
- When `Enable Profile Corrections` or `Auto Lens` is triggered, matching EXIF metadata populates the detected lens profile and applies distortion and vignetting correction.
- Even when no Lensfun profile matches the lens, `Remove Chromatic Aberration` estimates and corrects red/cyan and blue/yellow lateral edge fringing algorithmically.

#### FR-98: Integrated Auto Upright & Horizon Leveling (`Auto`, `Level`, `Vertical`, `Full`)

The Transform panel's `Off`, `Auto`, `Level`, `Vertical`, and `Full` Upright buttons detect dominant horizontal and vertical line segments (Canny/LSD + Hough orientation histogram) and write `CropAngle`, `TransformVertical`, `TransformHorizontal`, and `TransformConstrainCrop` to `develop_settings`.

**Consequences (testable):**
- `Level` computes the dominant near-horizontal tilt angle (`-15°..+15°`) and updates `CropAngle`.
- `Vertical` estimates vertical vanishing-point convergence and sets `TransformVertical`.
- `Full` applies both horizon leveling and vertical/horizontal perspective correction in one `"Upright Full"` History Step.
- `Auto` selects `Level`, `Vertical`, or `Full` based on line-confidence thresholds and avoids extreme distortion when line evidence is weak.

## 3. Non-Goals

- Neural/AI mask generation inside deterministic Auto Tone (covered in Epic 26 `prd-DarkLab-ai-image-corrections`).

## 4. Open Questions

None.
