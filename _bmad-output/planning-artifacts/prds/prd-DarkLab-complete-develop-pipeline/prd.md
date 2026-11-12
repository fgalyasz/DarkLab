---
title: DarkLab Complete End-to-End Develop Pipeline and Controls
status: final
created: 2026-11-11
updated: 2026-11-11
extends: prd-DarkLab-2026-10-10
epic: 24
parent_issue: 108
story_issues: [109, 110, 111, 112, 113, 114, 115, 116]
---

# PRD: Complete End-to-End Develop Pipeline and Controls

## 0. Document Purpose

This PRD adds FR-86 through FR-93 and completes the technical specification for FR-23 through FR-34. Currently, `DevelopPanel` only persists and renders a partial subset of `Basic` and `Crop` sliders while `Treatment (B&W)`, `Tone Curve`, `Color Mixer (HSL)`, `Color Grading`, `Detail`, `Lens Corrections`, `Transform`, `Effects`, `Calibration`, `Local Masks`, `Spot/Healing & Red Eye`, `Presets`, `Snapshots`, `Copy/Paste`, and `Soft Proofing` are UI shells or partially wired. This PRD defines complete, pixel-accurate, persistent, end-to-end operation for every Develop control across Preview, Export, Catalog SQLite, History, and XMP Sidecars.

## 1. Vision

Every control visible in the Develop module must work completely and predictably. Moving any slider, curve point, color wheel, checkbox, or local tool in Develop immediately updates the live Preview and Histogram within the responsiveness budget, persists to the Catalog's `develop_settings`, records a meaningful History Step, round-trips through XMP Sidecars, and renders identically during Export (`ADR-5`). No control in Develop may remain a dead placeholder.

## 2. Features

### 2.1 Complete Basic, Treatment, Tone Curve, HSL, and Color Grading Pipeline

#### FR-86: Full Basic panel, B&W Treatment, and live preview binding

All Basic controls (`Treatment: Color | B&W`, `WB: As Shot | Auto | Custom`, `Temp`, `Tint`, `Exposure`, `Contrast`, `Highlights`, `Shadows`, `Whites`, `Blacks`, `Texture`, `Clarity`, `Dehaze`, `Vibrance`, `Saturation`) update the Preview immediately on slider move, persist in `develop_settings`, and render identically in Export.

**Consequences (testable):**
- Every slider in `TONE_KEYS` (including `Highlights`, `Shadows`, `Whites`, `Blacks`, `Texture`, `Clarity`, `Dehaze`) is bound to live `_paint_preview()` updates in `DevelopPanel`.
- Choosing `B&W` sets `Treatment = "BW"` in `develop_settings`, converts the image to monochrome using channel luminance weights modulated by the HSL/B&W Mix bands, and restores full color when `Color` is re-selected.
- `Previous` restores the Develop Settings from the previously edited Photo, and `Reset` writes default settings to the Catalog and appends a `"Reset"` History Step.

#### FR-87: Parametric and Point Tone Curve (RGB, R, G, B)

The `Tone Curve` panel supports both Parametric sliders (`CurveHighlights`, `CurveLights`, `CurveDarks`, `CurveShadows`) and interactive Point Curves for `RGB`, `Red`, `Green`, and `Blue` channels.

**Consequences (testable):**
- Parametric values (`-100..100`) and channel control points (`[(x, y), ...]`) encode into `develop_settings`, generate a 256-entry LUT per channel in `src/imaging/tone_curve.py`, and apply after Basic Tone in both Preview and Export.
- Switching between `Parametric`, `Point Curve`, and `RGB / R / G / B` channel tabs preserves all stored points and slider values across restarts.

#### FR-88: 8-Band Color Mixer (HSL) and 4-Way Color Grading Wheels

The `Color Mixer` panel edits `Hue`, `Saturation`, and `Luminance` across all 8 Classic color bands (`Red`, `Orange`, `Yellow`, `Green`, `Aqua`, `Blue`, `Purple`, `Magenta`), and `Color Grading` edits `Hue`, `Saturation`, and `Luminance` on `Shadows`, `Midtones`, `Highlights`, and `Global` wheels plus `Blending` and `Balance`.

**Consequences (testable):**
- Clicking any of the 8 color dots in `Color Mixer` switches the active band and loads that band's stored `HSL_<Band>_Hue`, `HSL_<Band>_Sat`, and `HSL_<Band>_Lum` values (`-100..100`).
- Dragging a `ColorWheel` or its luminance/blending/balance sliders updates `Grade_<Zone>_Hue`, `Grade_<Zone>_Sat`, `Grade_<Zone>_Lum`, `Grade_Blending`, and `Grade_Balance`, renders via `src/imaging/hsl_mixer.py` and `src/imaging/color_wheels.py`, and persists per Photo.

### 2.2 Detail, Lens Corrections, Transform, Effects, and Calibration

#### FR-89: Detail (Sharpening & Noise Reduction) with 1:1 preview and unique keys

The `Detail` panel persists and renders Sharpening (`SharpAmount`, `SharpRadius`, `SharpDetail`, `SharpMasking`) and Noise Reduction (`NrLuminance`, `NrLuminanceDetail`, `NrLuminanceContrast`, `NrColor`, `NrColorDetail`, `NrColorSmoothness`).

**Consequences (testable):**
- Eliminates ambiguous trailing-space slider keys (`"Detail "`, `"Detail  "`) in favor of canonical keys (`SharpDetail`, `NrLuminanceDetail`, `NrColorDetail`).
- Edge-masked unsharp masking and bilateral/wavelet luminance + chroma noise reduction run in `src/imaging/detail.py` for both Preview (including 1:1 zoom view in Navigator/Loupe) and Export.

#### FR-90: Lens Corrections and Perspective Transform

The `Lens Corrections` panel applies profile-based or manual distortion (`LensDistortion`), chromatic aberration (`RemoveCA`), and lens vignetting (`LensVignetting`), and the `Transform` panel applies `TransformVertical`, `TransformHorizontal`, `TransformRotate`, `TransformAspect`, `TransformScale`, `TransformOffsetX`, `TransformOffsetY`, and `TransformConstrainCrop`.

**Consequences (testable):**
- Homography / radial warp in `src/imaging/lens_transform.py` transforms both Preview and Export identically.
- Enabling `Constrain Crop` automatically insets the crop rectangle to eliminate transparent/black border wedges introduced by perspective or rotation transforms.

#### FR-91: Post-Crop Vignetting, Film Grain, and Camera Calibration

The `Effects` panel applies Post-Crop Vignetting (`VignetteAmount`, `VignetteMidpoint`, `VignetteRoundness`, `VignetteFeather`, `VignetteHighlights`) and deterministic Film Grain (`GrainAmount`, `GrainSize`, `GrainRoughness`, seeded by `photo_id` so Preview and Export match), and `Calibration` applies `CalShadowsTint` and `CalRedHue`, `CalRedSat`, `CalGreenHue`, `CalGreenSat`, `CalBlueHue`, `CalBlueSat`.

**Consequences (testable):**
- Calibration primary matrix shifts and post-crop vignette/grain run in `src/imaging/effects_calibration.py` in the canonical render order (`ADR-5`).
- Settings persist in `develop_settings` and round-trip through XMP Sidecars.

### 2.3 Local Adjustments, Presets, Snapshots, History Persistence, and Soft Proofing

#### FR-92: Interactive Crop Overlay, Spot Heal/Clone, Red Eye, and Local Masks

The Develop tool row (`Crop`, `Spot`, `Red Eye`, `Mask`) activates interactive canvas overlays and tool drawers for local non-destructive edits.

**Consequences (testable):**
- `Crop` tool toggles an on-canvas draggable crop/straighten overlay synchronized with the Crop sliders.
- `Spot` tool records circular or brush Heal/Clone strokes (`HealStrokes` JSON list with source/target normalized coordinates, radius, feather, mode `heal|clone`) rendered in `src/imaging/healing.py`.
- `Red Eye` tool records pupil desaturation/darken ellipses (`RedEyeStrokes` JSON list) rendered in `src/imaging/red_eye.py`.
- `Mask` tool creates, edits, inverts, duplicates, and deletes `Brush`, `Linear Gradient`, `Radial Gradient`, `Color Range`, and `Luminance Range` masks (`Masks` JSON list, each with local tone/color deltas) rendered in `src/imaging/masking.py`.

#### FR-93: Develop Presets with Amount slider, Snapshots, Copy/Paste, Soft Proofing, and Persistent History

The left and center Develop controls (`Presets`, `Amount`, `Snapshots`, `History`, `Copy...`, `Paste`, `Soft Proofing`) are fully functional and persisted.

**Consequences (testable):**
- Built-in Presets across all 6 groups (`Color`, `Creative`, `B&W`, `Portrait`, `Landscape`, `Vivid`) and user-saved Presets apply as a single History Step, scaled proportionally by the `PresetAmount` slider (`0..200%`, default `100%`).
- `Snapshots` (`photo_snapshots` table in `catalog.sqlite`) allow creating, selecting, and deleting named setting snapshots per Photo.
- `History` steps persist in `photo_history` in `catalog.sqlite` so History survives application restarts.
- `Soft Proofing` simulates target output profile gamut warning overlays without altering stored `develop_settings`.

## 3. Non-Goals

- Proprietary Adobe `.dcp` camera profile parsing.
- Generative pixel synthesis (all tools remain deterministic or local-signal-based).

## 4. Open Questions

None.
