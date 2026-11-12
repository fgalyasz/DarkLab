# Addendum: Complete End-to-End Develop Pipeline and Controls

## 1. Canonical Render Order (`ADR-5` Complete Pipeline)

`src/imaging/pipeline.py` executes `render_develop_pipeline(image: np.ndarray, settings: dict[str, str], is_preview: bool = False) -> np.ndarray` in this exact order:
1. **Calibration (`src/imaging/effects_calibration.py`):** Shadow tint + RGB primary 3×3 matrix shift.
2. **Lens Corrections (`src/imaging/lens_transform.py`):** Chromatic aberration lateral channel alignment, radial distortion warp, and lens vignette lift.
3. **Transform & Crop (`src/imaging/lens_transform.py` + `src/imaging/crop.py`):** Perspective homography (`Vertical`, `Horizontal`, `Rotate`, `Aspect`, `Scale`, `OffsetX`, `OffsetY`), Constrain Crop inset, and Straighten + Crop box.
4. **Spot Healing & Red Eye (`src/imaging/healing.py`, `src/imaging/red_eye.py`):** Source-patch Poisson/feather blend for Heal/Clone strokes and Red Eye pupil correction.
5. **White Balance & Treatment (`src/imaging/color_grade.py`, `src/imaging/treatment.py`):** Temperature/Tint chromatic adaptation and Color vs. B&W conversion.
6. **Basic Tone & Presence (`src/imaging/tone.py`, `src/imaging/presence.py`):** Exposure, Contrast, Highlights, Shadows, Whites, Blacks, Texture, Clarity, Dehaze, Vibrance, Saturation.
7. **Tone Curve (`src/imaging/tone_curve.py`):** Parametric 4-region spline + RGB, R, G, B point LUTs.
8. **Color Mixer / HSL (`src/imaging/hsl_mixer.py`):** 8-band soft-windowed Hue, Saturation, and Luminance shifts (or B&W Mix weights when `Treatment == "BW"`).
9. **Color Grading (`src/imaging/color_wheels.py`):** Shadows, Midtones, Highlights, and Global tinting with Luminance, Blending, and Balance.
10. **Local Masks (`src/imaging/masking.py`):** Alpha-blended regional application of local Tone/Presence/HSL/Detail deltas for each active Mask.
11. **Detail (`src/imaging/detail.py`):** Luminance/Color noise reduction followed by edge-masked Unsharp Mask sharpening.
12. **Effects (`src/imaging/effects_calibration.py`):** Post-Crop Vignetting (with highlight preservation) and deterministic Film Grain.

## 2. Canonical Settings Schema (`src/develop/settings_schema.py`)

All Develop controls map to flat string keys in `develop_settings` (with JSON-serialized lists for `CurvePoints_*`, `Masks`, `HealStrokes`, and `RedEyeStrokes`), ensuring 100% compatibility with `read_develop_settings`, `write_develop_settings`, `DevelopHistory`, and XMP Sidecar serialization.

## 3. Cost-Effective Model Implementation Blueprint

Each story in Epic 24 is isolated to one stage of the pipeline:
- Story 24.1: Canonical `settings_schema.py`, full `Basic` live preview binding, `B&W` treatment, and `Reset`/`Previous` persistence (`tests/test_develop_basic_complete.py`).
- Story 24.2: `src/imaging/tone_curve.py` + `ToneCurveWidget` binding (`tests/test_tone_curve.py`).
- Story 24.3: `src/imaging/hsl_mixer.py` + `src/imaging/color_wheels.py` + 8-band dot switcher & wheel bindings (`tests/test_hsl_and_grading.py`).
- Story 24.4: `src/imaging/detail.py` + unique Detail control keys + 1:1 Navigator/Preview zoom (`tests/test_detail_pipeline.py`).
- Story 24.5: `src/imaging/lens_transform.py` + Lensfun/manual lens & Transform + Constrain Crop (`tests/test_lens_transform.py`).
- Story 24.6: `src/imaging/effects_calibration.py` + Vignette, Grain, and Calibration primaries (`tests/test_effects_calibration.py`).
- Story 24.7: `src/imaging/masking.py`, `src/imaging/healing.py`, `src/imaging/red_eye.py` + interactive tool row (`Crop`, `Spot`, `Red Eye`, `Mask`) (`tests/test_local_adjustments.py`).
- Story 24.8: Built-in & custom `Presets` with `Amount` slider, persistent `Snapshots` & `History` tables in SQLite, `Copy...`/`Paste` dialog, `Soft Proofing`, and unified `pipeline.py` in Preview + Export (`tests/test_presets_snapshots_pipeline.py`).
