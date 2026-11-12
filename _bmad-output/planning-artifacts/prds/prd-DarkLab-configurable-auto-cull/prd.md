---
title: DarkLab Configurable Auto-Cull on Import and Library
status: final
created: 2026-11-11
updated: 2026-11-11
extends: prd-DarkLab-2026-10-10
epic: 23
parent_issue: 102
story_issues: [103, 104, 105, 106, 107]
---

# PRD: Configurable Auto-Cull on Import and Library

## 0. Document Purpose

This PRD adds FR-80 through FR-85. It defines configurable automatic selection (Auto-Cull) of imported photographs in both the Import dialog ("Assisted Culling") and the Library module, evaluating eyes open/blink state, smile/expression, subject & overall sharpness, exposure health, face framing, and burst/duplicate grouping to assign non-destructive Cull marks (`Flag`, `Rating`, `Color Label`). Technical scoring formulas, SQLite storage, and cost-effective model decomposition live in `addendum.md`.

## 1. Vision

A wedding or event photographer imports 500–2,000 frames from a shoot and should not spend three hours checking every frame at 1:1 for blinked eyes, motion blur, or 10 near-identical burst shots. DarkLab evaluates each Photo locally against Photographer-configured criteria and weights, groups bursts, picks the strongest frame(s), flags defects as Rejected or Unflagged, and lets the Photographer inspect, filter, adjust thresholds, or override any mark before or after Import commit — without ever modifying an Original file or requiring a network connection.

## 2. Features

### 2.1 Configurable Culling Criteria and Profiles

#### FR-80: Culling criteria and weight configuration

The Photographer can enable, weight (0–100), and set minimum pass thresholds for each Auto-Cull criterion, and save or select named Culling Profiles (built-in: `Portrait & Wedding`, `Event & Action`, `Landscape & Architecture`, `Custom`).

**Consequences (testable):**
- The configurable criteria are:
  - `sharpness_weight` and `sharpness_min` (0–100; measures subject/face edge energy when a face/subject is present, or global frame Tenengrad/Laplacian sharpness when no face is present).
  - `eyes_open_weight` and `eyes_open_min` (0–100; eye-aspect-ratio / open-eye confidence across detected faces, plus `require_all_eyes_open: bool` for group shots).
  - `smile_weight` and `smile_min` (0–100; mouth/expression positivity score on detected faces; ignored when weight is 0 or no face is present).
  - `exposure_weight` and `exposure_min` (0–100; penalizes severe highlight/shadow clipping and extreme under/over-exposure).
  - `framing_weight` and `framing_min` (0–100; evaluates face/subject size, gaze orientation, and edge cut-off).
- Changing weights or switching the active Culling Profile recomputes composite scores and suggested marks from cached per-photo metric vectors in under 50 ms for 500 Photos without re-decoding Originals.
- Culling Profile settings persist in the Catalog's `settings.json` under the `auto_cull` key and round-trip across restarts.

#### FR-81: Per-Photo quality metric extraction and caching

DarkLab computes deterministic per-Photo quality metrics (`sharpness_score`, `face_count`, `eyes_open_score`, `all_eyes_open`, `smile_score`, `exposure_score`, `framing_score`, `perceptual_hash`) off the UI thread from the index preview or decoded frame and stores them in `catalog.sqlite`.

**Consequences (testable):**
- Metrics are stored in a `photo_cull_metrics` table keyed by `photo_id` and `content_hash`.
- Re-running Auto-Cull on Photos whose `content_hash` already has cached metrics skips image decoding and re-evaluates rules immediately.
- If no face is detected on a Photo (`face_count == 0`), `eyes_open_score` and `smile_score` are excluded from the weighted denominator so non-portrait shots are not penalized for lacking faces.
- Original files and their SHA-256 hashes remain untouched.

#### FR-82: Burst and near-duplicate grouping with best-shot selection

Auto-Cull groups sequential or visually similar Photos into burst groups using capture-time proximity (`burst_time_window_sec`, default 3.0 s) and perceptual hash distance (`burst_hamming_max`, default 10), then selects the highest-scoring Photo(s) per burst.

**Consequences (testable):**
- Within each burst group, the top `max_picks_per_burst` (default 1) Photo that meets minimum thresholds receives `pick = "accepted"`.
- Other Photos in the same burst remain `pick = "none"` (or `"rejected"` if below hard defect thresholds).
- Disabling burst grouping evaluates every Photo independently against the profile's pick and reject thresholds.

#### FR-83: Automatic Flag, Rating, and Color Label assignment rules

Auto-Cull maps composite scores and hard defect triggers (such as blinked eyes or severe blur below `reject_sharpness_floor`) to DarkLab Cull marks (`pick`, `rating`, `color`).

**Consequences (testable):**
- Photos failing a hard defect rule (e.g., `sharpness_score < reject_sharpness_floor` or `all_eyes_open == False` when `reject_closed_eyes` is enabled) receive `pick = "rejected"`.
- Photos meeting or exceeding `pick_score_min` (and winning their burst group when burst mode is on) receive `pick = "accepted"`.
- When `auto_rate_stars` is enabled, composite score bands map deterministically to `rating` `"1"` through `"5"`.
- When `preserve_manual_marks` is enabled (default `True`), Photos that already have a Photographer-set Flag or Rating are not overwritten unless the Photographer chooses "Overwrite existing marks".

#### FR-84: Import Assisted Culling workflow

In the Import dialog (`Assisted Culling` mode and the Import side panel), the Photographer can run or enable Auto-Cull on candidate files before or during Import commit.

**Consequences (testable):**
- In `Assisted Culling` mode, candidate files display their computed quality badges (Sharpness, Eyes, Smile, Burst winner) and suggested Pick/Reject state.
- The Photographer can filter candidates by suggested Pick/Reject/Rating, tweak criteria sliders, or opt to import only Picked/non-Rejected files or import all files with marks pre-applied to the Catalog.

#### FR-85: Library Auto-Cull batch action and explainable score badge

From the Library module, the Photographer can run Auto-Cull on the current Folder, Collection, or multi-selection and inspect why each Photo was picked or rejected.

**Consequences (testable):**
- Running Auto-Cull in Library updates Catalog marks (`write_mark`) off the UI thread with progress reporting and cancellation support.
- Each Photo's tooltip/info summary shows the breakdown (`Composite: 86 | Sharpness: 92 | Eyes: Open (95) | Smile: 78 | Exposure: 88`).

## 3. Non-Goals

- Cloud-hosted culling APIs or uploading user photographs to external servers.
- Deleting Original files from disk automatically when a Photo is marked `rejected` (rejection only sets the Catalog `pick` mark).

## 4. Open Questions

None.
