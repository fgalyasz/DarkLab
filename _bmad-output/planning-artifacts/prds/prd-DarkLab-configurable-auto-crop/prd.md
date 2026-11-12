---
title: DarkLab Configurable Auto-Crop and Smart Framing
status: final
created: 2026-11-11
updated: 2026-11-11
extends: prd-DarkLab-2026-10-10
epic: 27
parent_issue: 128
story_issues: [129, 130, 131, 132]
---

# PRD: Configurable Auto-Crop and Smart Framing

## 0. Document Purpose

This PRD adds FR-105 through FR-109. It defines configurable automatic cropping (`Auto-Crop`) in Develop and Library, allowing the Photographer to configure target aspect ratio, composition rule (Rule of Thirds, Golden Ratio, Center, Portrait Headroom, Horizon Split), subject/face padding and headroom, look-room bias, group-safety guard, and straighten-constrained bounding boxes.

## 1. Vision

Cropping 300 portrait, event, or product photos to consistent framing (such as 4:5 vertical portraits with 12% headroom and eyes on the upper third line, or leveled landscapes with a 1/3 horizon) is repetitive mechanical work. DarkLab's Configurable Auto-Crop detects subjects, faces, eyes, and horizon lines, solves for the optimal crop rectangle that satisfies the Photographer's chosen rules and aspect ratio without cutting off group members or exposing black rotation triangles, and writes standard non-destructive Crop Develop Settings (`CropLeft`, `CropTop`, `CropRight`, `CropBottom`, `CropAngle`, `CropAspectLock`).

## 2. Features

### 2.1 Configurable Auto-Crop Rules, Aspect Ratios, and Subject Framing

#### FR-105: Auto-Crop configuration model and presets

The Photographer can configure Auto-Crop settings and save/load named Auto-Crop Presets (built-in: `Portrait Rule of Thirds (4:5)`, `Headshot Tight (4:5)`, `Wedding Group Safe (3:2)`, `Square Social (1:1)`, `Cinematic 16:9`, `Landscape Horizon (3:2)`):
- `aspect_ratio`: `Original`, `1:1`, `4:5`, `5:7`, `2:3`, `3:2`, `4:3`, `16:9`, `9:16`, or custom `W:H`.
- `composition_rule`: `rule_of_thirds`, `golden_ratio`, `center_subject`, `portrait_headroom`, `horizon_thirds`.
- `headroom_pct`: `2..35` (default `12%` above top of head/hair in portrait modes).
- `padding_pct`: `2..40` (default `10%` minimum margin around the detected subject/group bounding box).
- `look_room_bias`: `0..100` (shifts horizontal framing to leave extra space in the direction the subject's face/gaze is oriented).
- `auto_level_horizon`: `bool` (automatically applies horizon straighten angle before solving for the crop box).
- `never_cut_faces`: `bool` (default `True`; expands the crop box or falls back to a wider framing so no detected face bounding box is intersected by a crop edge).

**Consequences (testable):**
- Auto-Crop configuration persists in the Catalog's `settings.json` (`auto_crop` key) and round-trips cleanly.
- Invalid or out-of-range values are clamped to safe bounds (`MAX_EDGE`, `MAX_ANGLE`).

#### FR-106: Subject, Face, Eye-Line, and Saliency Anchor Detection

Auto-Crop locates the primary anchor point (eye-line midpoint for single/group faces, saliency centroid for non-face subjects, or horizon line for landscapes) and the union bounding box of all subjects to preserve.

**Consequences (testable):**
- On a single portrait, the anchor is the midpoint between the detected eyes, and the top of the head is estimated from the face box.
- On a group photo, the subject bounding box is the union of all detected faces/persons, and `never_cut_faces` prevents any face from being bisected by the crop rectangle.
- When no face is present, visual saliency (spectral residual / gradient energy map) provides the subject bounding box and centroid.

#### FR-107: Composition-Rule and Aspect-Ratio Crop Solver

Given image dimensions `(width, height)`, rotation `angle`, target `aspect_ratio`, `composition_rule`, and detected subject anchors, the Auto-Crop solver computes exact `CropSettings(left, top, right, bottom, angle, locked=True)`.

**Consequences (testable):**
- Placing an anchor on `rule_of_thirds` aligns the eye-line or subject centroid with the nearest upper-third (`y = 1/3`) and vertical third (`x = 1/3` or `2/3`, chosen by `look_room_bias`) grid intersection while keeping the crop window inside the valid image area.
- The resulting pixel box from `crop_box((width, height), crop)` matches the requested `aspect_ratio` within `±1%` (quantization limit of integer percent crop edges, or exact when fractional/sub-percent precision is used).

#### FR-108: Straighten-Constrained Inscribed Bounding Box

When `auto_level_horizon` is enabled or a non-zero `CropAngle` is present, the Auto-Crop solver constrains the crop box to the largest inscribed valid image region inside the rotated photograph so no black background wedges appear at the corners.

**Consequences (testable):**
- For any `angle` in `[-45, 45]`, every corner of the resulting Auto-Crop rectangle lies inside the original rotated photograph's valid pixel polygon.
- Original files and hashes remain untouched.

#### FR-109: Develop and Library Auto-Crop UI and History Integration

The Develop `Crop` panel includes an `Auto Crop` button and a collapsible/popup `Auto-Crop Settings` configuration bar (Preset, Aspect Ratio, Composition Rule, Headroom %, Padding %, Auto-Level checkbox).

**Consequences (testable):**
- Clicking `Auto Crop` updates `CropLeft`, `CropTop`, `CropRight`, `CropBottom`, `CropAngle`, and `CropAspectLock`, refreshes the Preview and Histogram immediately, and records a single `"Auto Crop"` History Step.
- Clicking `Reset` in the Crop panel restores the uncropped full frame.

## 3. Non-Goals

- Outpainting or generative canvas extension outside the Original image bounds.

## 4. Open Questions

None.
