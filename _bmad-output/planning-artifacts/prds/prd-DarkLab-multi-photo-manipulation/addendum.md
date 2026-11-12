# Addendum: Multi-Photo Batch Image Manipulation and Sync

## 1. Architecture & Package Placement

- `src/develop/sync_groups.py` — Defines the 14 selectable sync groups (`SYNC_GROUPS: dict[str, tuple[str, ...]]`), `filter_settings_by_groups(settings, groups)`, and `sync_settings_to_photos(catalog, primary_id, target_ids, groups)`.
- `src/develop/batch_adjust.py` — Implements `apply_relative_delta(catalog, photo_ids, deltas)`, `apply_absolute_settings(catalog, photo_ids, changes)`, and `match_total_exposure(catalog, primary_id, target_ids, luma_lookup, exif_lookup)`.
- `src/develop/batch_processor.py` — Background-safe batch orchestrator `run_batch_photo_operation(catalog, photo_ids, operation_fn, progress_cb, cancel_check) -> BatchResult` that skips missing Originals (`missing_photo_ids`), applies per-photo computed settings (Auto Tone, Auto WB, Auto Upright, Auto-Crop, AI Auto-Develop, AI Denoise, Adaptive Presets), records a History Step on each Photo, and invalidates stale preview cache entries.
- `src/ui/dialogs/sync_settings_dialog.py` — Modal dialog for `Sync...` and `Copy...` group selection with `Check All` / `Check None`.

## 2. Cost-Effective Model Implementation Blueprint

- Story 28.1: Multi-selection state `(primary_path, selected_paths)` in `FilmstripWidget` and `GridImageWidget` + `tests/test_multi_selection.py`
- Story 28.2: `src/develop/sync_groups.py` + `SyncSettingsDialog` + `Auto-Sync` broadcast in `DevelopPanel` + `tests/test_sync_settings.py`
- Story 28.3: `src/develop/batch_adjust.py` (Relative delta adjustments, Absolute Quick Develop, and `Match Total Exposure`) + `tests/test_batch_adjust.py`
- Story 28.4: `src/develop/batch_processor.py` (Per-photo computed Batch Auto Tone, Auto WB, Auto Upright, Configurable Auto-Crop, and AI Corrections with progress/cancel) + `tests/test_batch_processor.py`
- Story 28.5: Wire Library `Quick Develop` and Develop batch toolbar/context menu actions (`Sync...`, `Auto-Sync`, `Match Total Exposure`, `Batch Auto-Crop`, `Batch Auto-Tone`, `Batch AI Enhance`) + `tests/test_multi_photo_ui.py`
