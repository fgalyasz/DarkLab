---
title: DarkLab Multi-Photo Batch Image Manipulation and Sync
status: final
created: 2026-11-11
updated: 2026-11-11
extends: prd-DarkLab-2026-10-10
epic: 28
parent_issue: 133
story_issues: [134, 135, 136, 137, 138]
---

# PRD: Multi-Photo Batch Image Manipulation and Sync

## 0. Document Purpose

This PRD adds FR-110 through FR-115 and expands FR-20 (`Quick Develop`) and FR-32 (`Copy/Paste Develop Settings`). It extends all Develop, Auto-Correction, AI Correction, and Auto-Crop image manipulation features from a single Photo to multiple selected Photos across both the Library module and the Develop module.

## 1. Vision

A Photographer never edits a 500-photo shoot one frame at a time from scratch. They select a lighting sequence of 30 frames in the Filmstrip or Library Grid and either:
1. **Sync / Auto-Sync** specific Develop sections from a reference frame to the rest of the selection,
2. Apply **Relative (delta) or Absolute** adjustments across all selected Photos in Quick Develop,
3. **Match Total Exposure** across a variable-light series, or
4. Run **Batch Auto-Tone, Batch Auto-WB, Batch Auto-Upright, Batch Configurable Auto-Crop, or Batch AI Corrections** so DarkLab computes the optimal per-photo settings for each selected frame in parallel.

## 2. Features

### 2.1 Multi-Selection in Filmstrip/Grid, Selective Sync, and Auto-Sync

#### FR-110: Multi-Photo Selection in Develop Filmstrip and Library Grid

Both `GridImageWidget` (Library) and `FilmstripWidget` (Library & Develop) support multi-photo selection (`Cmd/Ctrl+Click` toggle, `Shift+Click` range, `Cmd/Ctrl+A` select all, `Cmd/Ctrl+D` deselect), distinguishing the **Primary (most-selected) Photo** (shown in Loupe/Develop preview) from the **Secondary selected Photos**.

**Consequences (testable):**
- Selecting a range of 10 Photos in Library and switching to Develop preserves the 10-photo selection and active Primary Photo in the Develop Filmstrip.
- `selection_state()` returns `(primary_path: Path | None, selected_paths: list[Path])`.

#### FR-111: Selective `Sync...` Dialog and `Copy...` / `Paste` Across Multiple Photos

When 2 or more Photos are selected, the Develop toolbar offers `Sync...` (and `Paste` applies copied settings to all selected Photos). The `Sync...` / `Copy...` dialog lets the Photographer check/uncheck which Develop setting groups to synchronize:
`Treatment & WB`, `Basic Tone`, `Presence`, `Tone Curve`, `Color Mixer (HSL)`, `Color Grading`, `Detail`, `Lens Corrections`, `Transform`, `Crop`, `Effects`, `Calibration`, `Masks`, `Spot Healing & Red Eye`.

**Consequences (testable):**
- Only keys belonging to the checked groups are merged (`merge_develop_settings`) from the Primary Photo into each Secondary selected Photo; unchecked groups on target Photos remain intact.
- Each updated target Photo records one `"Sync Settings"` (or `"Paste Settings"`) History Step.
- Missing Originals are skipped and reported in the batch summary without aborting the remaining Photos.

#### FR-112: Develop `Auto-Sync` Mode

A checkable `Auto-Sync` toggle next to `Sync...` in Develop broadcasts any live control change (Tone slider, WB, Curve, HSL, Grading, Detail, Transform, Effects, Calibration, Preset, Reset) made on the Primary Photo immediately to all currently selected Photos.

**Consequences (testable):**
- With `Auto-Sync` ON and 5 Photos selected, changing `Exposure` to `+45` on the Primary Photo writes `Exposure = "45"` (merging only the changed key) to all 5 Photos and records a History Step on each.
- With `Auto-Sync` OFF, editing a control modifies only the Primary Photo.

### 2.2 Relative Batch Quick Develop, Match Total Exposure, and Per-Photo Computed Batch Actions

#### FR-113: Relative (Delta) and Absolute Multi-Photo Quick Develop

The Library `Quick Develop` panel operates on all selected Photos and supports:
- **Saved Preset** application across the selection.
- **White Balance** dropdown (`As Shot`, `Auto`, `Daylight`, `Cloudy`, `Shade`, `Tungsten`, `Fluorescent`, `Flash`).
- **Relative step buttons** (`<<`, `<`, `>`, `>>`) and **Absolute sliders** for `Exposure`, `Contrast`, `Highlights`, `Shadows`, `Whites`, `Blacks`, `Clarity`, `Vibrance`, and `Saturation`.

**Consequences (testable):**
- Relative step buttons add a signed delta (`Δ`) to each Photo's own existing stored value (e.g., if Photo 1 has `Exposure = 10` and Photo 2 has `Exposure = -20`, clicking `+1/3 EV (+33)` sets Photo 1 to `43` and Photo 2 to `13`), clamped to the control's legal range.
- Each affected Photo gains one History Step and rebuilds its thumbnail/preview asynchronously.

#### FR-114: Match Total Exposure Across Selected Photos

The `Match Total Exposure` command normalizes perceived brightness across all selected Photos to match the Primary (most-selected) Photo.

**Consequences (testable):**
- Using EXIF exposure value ($\text{EV} = \log_2(N^2 / t) - \log_2(\text{ISO}/100)$) when present, and median scene luminance from the decoded image when EXIF exposure tags are absent or lighting changed, DarkLab computes per-photo `Exposure` slider offsets so each secondary Photo's post-exposure median luminance matches the Primary Photo's post-exposure median luminance within `±3` luma levels.
- Writes only the `Exposure` key in `develop_settings` and records a `"Match Total Exposure"` History Step on each secondary Photo.

#### FR-115: Per-Photo Computed Batch Auto-Corrections, Batch Auto-Crop, and Batch AI Corrections

The Photographer can select multiple Photos in Library or Develop and run **Batch Auto Tone**, **Batch Auto WB**, **Batch Auto Upright**, **Batch Auto-Crop** (using the active `AutoCropConfig`), **Batch AI Auto-Develop**, **Batch AI Denoise**, or **Batch AI Adaptive Preset**.

**Consequences (testable):**
- Unlike static `Sync`, Batch Auto/AI/Auto-Crop evaluates the algorithm **individually on each Photo's own pixels/anchors** (so Photo A gets Photo A's face-centered crop and histogram auto-tone, while Photo B gets Photo B's face-centered crop and histogram auto-tone).
- Execution runs on a background worker pool with a progress bar, per-file completion count, cancellation button, and summary report (`Updated M photos, skipped K missing Originals`).
- EveryOriginal file's SHA-256 hash is unchanged before and after any batch operation.

## 3. Non-Goals

- Cross-Catalog batch editing (batch operations apply within the currently open Catalog).

## 4. Open Questions

None.
