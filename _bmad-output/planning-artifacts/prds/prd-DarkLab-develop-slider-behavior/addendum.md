# Addendum — Cost-effective implementation blueprint

## Target files

- `src/ui/widgets/slider_row.py` — `DevelopSlider` double-click + arrow/Shift-arrow
- `src/imaging/basic_tone.py` — `BasicTone`, `apply_basic_tone`
- `src/ui/preview_image.py` — `basic_tone_image` / `grade_image(..., basic=)`
- `src/imaging/tone.py` / `src/exporting/render.py` — export path
- `src/ui/panels/develop_panel.py` — bind all `TONE_KEYS` to `_paint_preview`
- `tests/test_basic_tone.py`, `tests/test_slider_row.py`

## Contracts

```python
FINE_STEP = 1
COARSE_STEP = 10
BasicTone.from_tone(tone: dict[str, int]) -> BasicTone
apply_basic_tone(pixels: np.ndarray, tone: BasicTone) -> np.ndarray
```
