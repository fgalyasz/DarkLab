# Addendum: Configurable Auto-Cull on Import and Library

## 1. Architecture & Package Placement

- `src/culling/criteria.py` — `CullCriteria` dataclass, built-in presets (`PORTRAIT_WEDDING`, `EVENT_ACTION`, `LANDSCAPE`, `CUSTOM`), JSON serialization for `settings.json` (`auto_cull` key).
- `src/culling/metrics.py` — `PhotoCullMetrics` dataclass and deterministic image evaluators (Tenengrad/Laplacian sharpness, luminance histogram exposure health, 64-bit dHash perceptual hash, and OpenCV cascade / lightweight local landmark detector for face box, eye openness ratio, and mouth smile curvature).
- `src/culling/burst.py` — `group_bursts(items, time_window_sec, max_hamming)` and burst winner ranking.
- `src/culling/scorer.py` — `compute_composite_score(metrics, criteria)` and `decide_cull_Decision(metrics, criteria, is_burst_winner)`.
- `src/catalog/cull_metrics_store.py` — SQLite persistence for `photo_cull_metrics` table in `catalog.sqlite`.
- `src/ui/dialogs/auto_cull_dialog.py` — Configurable criteria & profile dialog used by both Import (`Assisted Culling`) and Library (`Auto-Cull...`).

## 2. Scoring Math (Deterministic)

1. **Sharpness (`0..100`):** Variance of Laplacian / Sobel gradient magnitude on grayscale image (or face ROI × 1.3 + full frame × 0.7 when `face_count > 0`), normalized via piece-wise linear clamping to `0..100`.
2. **Eyes Open (`0..100`):** Vertical-to-horizontal eye opening ratio (EAR) / upper-lower eyelid contrast inside detected eye regions. `all_eyes_open = min(eye_scores) >= criteria.eyes_open_min`.
3. **Smile (`0..100`):** Corner-of-mouth lift and mouth-width ratio inside lower half of face ROI, normalized `0..100`.
4. **Exposure (`0..100`):** `100 - clip_penalty - midtone_deviation_penalty`, where `clip_penalty` counts pixels `< 4` or `> 251` and `midtone_deviation_penalty` measures distance of median luma from `[85..170]`.
5. **Framing (`0..100`):** Evaluates whether detected faces are at least `min_face_margin_pct` away from frame borders and occupy a target area ratio.
6. **Composite Score:** Weighted average of active criteria. When `face_count == 0`, face-dependent weights (`eyes_open_weight`, `smile_weight`) are set to `0` for that Photo so denominator is `sharpness_weight + exposure_weight + framing_weight`.

## 3. Cost-Effective Model Implementation Blueprint

Each story in Epic 23 touches at most 1–2 small domain modules with functions ≤ 10 lines:
- Story 23.1: `src/culling/criteria.py` + `tests/test_cull_criteria.py`
- Story 23.2: `src/culling/metrics.py` + `tests/test_cull_metrics.py`
- Story 23.3: `src/culling/scorer.py` & `src/culling/burst.py` + `tests/test_cull_scorer.py`
- Story 23.4: `src/catalog/cull_metrics_store.py` + schema migration + `tests/test_cull_metrics_store.py`
- Story 23.5: Wire `ImportDialog` (`Assisted Culling`) & `LibraryBrowserPanel` (`Auto-Cull...` dialog) + `tests/test_auto_cull_ui.py`
