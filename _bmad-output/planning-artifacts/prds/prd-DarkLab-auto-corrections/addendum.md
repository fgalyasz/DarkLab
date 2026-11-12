# Addendum: Automatic Image Corrections

## 1. Architecture & Package Placement

- `src/develop/auto_tone.py` — Pure NumPy histogram analyzer: `compute_auto_tone(pixels: np.ndarray, include_presence: bool = True) -> dict[str, int]`.
- `src/develop/auto_wb.py` — Illuminant estimator: `compute_auto_wb(pixels: np.ndarray) -> tuple[int, int]` returning `(temp, tint)`.
- `src/develop/auto_upright.py` — Line-segment orientation & vanishing-point solver: `compute_upright(pixels: np.ndarray, mode: str) -> dict[str, str]`.
- `src/develop/auto_lens.py` — EXIF-to-Lensfun matcher and lateral chromatic aberration estimator: `compute_auto_lens(exif: dict[str, str], pixels: np.ndarray) -> dict[str, str]`.

## 2. Algorithmic Specifications

1. **Auto Tone (`src/develop/auto_tone.py`):**
   - Convert RGB to linear luminance $Y = 0.2126 R + 0.7152 G + 0.0722 B$.
   - Compute percentiles $P_{0.5}, P_{10}, P_{50}, P_{90}, P_{99.5}$.
   - `Exposure`: shifts $P_{50}$ toward target mid-gray ($118 / 255$), clamped to `[-250, +250]`.
   - `Highlights`: negative recovery proportional to pixel fraction above $P_{95}$ after exposure shift, clamped `[-100, +40]`.
   - `Shadows`: positive lift proportional to pixel fraction below $P_{15}$, clamped `[-40, +100]`.
   - `Whites` & `Blacks`: map post-tone $P_{99.5} \to 250$ and $P_{0.5} \to 5$, clamped `[-80, +80]`.
   - `Contrast`: gentle S-curve boost when interquartile range $(P_{75} - P_{25})$ is narrow, clamped `[-30, +45]`.
2. **Auto White Balance (`src/develop/auto_wb.py`):**
   - Exclude clipped pixels ($< 15$ or $> 240$) and high-saturation pixels ($S > 0.45$).
   - Compute mean $R/G$ and $B/G$ ratios on remaining neutral candidate pixels; map $B/R$ log-ratio to `Temp` (`2000..50000`, neutral `5500`) and $G / \sqrt{R \cdot B}$ log-ratio to `Tint` (`-150..150`, neutral `0`).
3. **Auto Upright (`src/develop/auto_upright.py`):**
   - Extract gradient edges on a 640px working copy; group segments into near-horizontal ($|\theta| \le 15^\circ$) and near-vertical ($|\theta - 90^\circ| \le 20^\circ$).
   - Weighted median of near-horizontal angles yields `CropAngle`; vertical convergence slope yields `TransformVertical`.

## 3. Cost-Effective Model Implementation Blueprint

- Story 25.1: `src/develop/auto_tone.py` + `src/develop/auto_wb.py` + `tests/test_auto_tone_wb.py`
- Story 25.2: `src/develop/auto_upright.py` + Transform Upright mode buttons wiring (`Off`, `Auto`, `Level`, `Vertical`, `Full`) + `tests/test_auto_upright.py`
- Story 25.3: `src/develop/auto_lens.py` + chromatic aberration & Lensfun profile lookup + `tests/test_auto_lens.py`
- Story 25.4: One-click `Auto` button in Develop Basic panel, Library Quick Develop `Auto Tone`, and Import optional Auto-Correction preset + `tests/test_auto_correction_ui.py`
