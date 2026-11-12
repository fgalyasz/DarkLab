# Addendum: AI Image Correction and Enhancement Suite

## 1. Architecture & Local-First AI Adapter (`src/ai/`)

To guarantee that DarkLab runs on macOS, Windows, and Linux with zero network requirement (`ADR-8`) and deterministic unit tests (`NFR-8`), all AI features sit behind `src/ai/`:
- `src/ai/model_registry.py` — Manages local model backends (bundled lightweight ONNX / OpenCV vision backends + deterministic multi-scale vision fallback when optional heavy weights are not installed).
- `src/ai/semantic_masks.py` — `segment_subject`, `segment_sky`, `segment_background`, and `segment_face_parts` returning normalized `0.0..1.0` float alpha maps cached by `(photo_id, content_hash, mask_kind)`.
- `src/ai/scene_corrector.py` — `classify_scene(pixels, exif)` and `compute_ai_auto_develop(pixels, exif, strength)` returning global `develop_settings` + semantic mask adjustments.
- `src/ai/portrait_retouch.py` — Frequency-separation skin smoothing (`apply_skin_retouch`), eye clarity/catchlight boost, dark-circle lift, and teeth desaturation/whitening.
- `src/ai/denoise_sharpen.py` — Multi-scale wavelet / NL-means / edge-guided AI denoise and Richardson-Lucy / edge-aware deblur pass.
- `src/ai/spot_detector.py` — LoG (Laplacian of Gaussian) blob detector on sky/backdrop and skin masks producing `HealStroke` candidates with optimal low-gradient source offsets.
- `src/ai/adaptive_presets.py` — Evaluates dynamic semantic masks per Photo and binds preset local adjustment deltas scaled by `PresetAmount`.

## 2. Cost-Effective Model Implementation Blueprint

- Story 26.1: `src/ai/model_registry.py` + `src/ai/semantic_masks.py` (Subject, Sky, Background, Face-parts segmentation & caching) + `tests/test_ai_semantic_masks.py`
- Story 26.2: `src/ai/scene_corrector.py` (AI Scene classification, AI Auto-Develop, and Subject Relight) + `tests/test_ai_scene_corrector.py`
- Story 26.3: `src/ai/portrait_retouch.py` (Frequency-separation skin smoothing, eyes, dark circles, teeth, lips) + `tests/test_ai_portrait_retouch.py`
- Story 26.4: `src/ai/denoise_sharpen.py` + `src/ai/spot_detector.py` (AI Denoise, AI Sharpen/Deblur, and Sensor Dust/Blemish Auto-Heal) + `tests/test_ai_denoise_and_spots.py`
- Story 26.5: `src/ai/adaptive_presets.py` + Develop UI panels (`AI Corrections`, `AI Masking`, `Adaptive Presets`) + `tests/test_ai_adaptive_presets.py`
