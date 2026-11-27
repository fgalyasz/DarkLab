# Technical Addendum — Classic Darkroom Panel Design

## Exact Color & Metric Tokens

| Element | Token / Selector | Value |
| --- | --- | --- |
| Module bar | `StyleSheet.MODULE_BAR` | `rgb(14, 14, 14)`, bottom `1px solid rgb(32, 32, 32)` |
| Center canvas / preview | `_empty_preview`, `QWidget` | `rgb(51, 51, 51)` / `rgb(50, 50, 50)` |
| Panel column gutter | `#panelColumn`, `#toolStack` | `rgb(50, 50, 50)` |
| Panel header | `#panelHeader` | `rgb(50, 50, 50)`, top `1px solid rgb(62, 62, 62)`, bottom `1px solid rgb(12, 12, 12)`, `border-radius: 0px` |
| Panel header title | `#panelTitle` | `rgb(210, 210, 210)`, `11px`, `font-weight: 500` |
| Panel body surface | `#collapsibleSection`, `#sectionBody` | `rgb(80, 80, 80)`, outer `1px solid rgb(14, 14, 14)`, inner top `1px solid rgb(92, 92, 92)` |
| Major etched divider | `EtchedDivider` (`kind="major"`) | `2px` tall: `1px rgb(24, 24, 24)` + `1px rgb(92, 92, 92)` |
| Soft intra-group divider | `EtchedDivider` (`kind="soft"`) | `12px` row containing `1px rgb(70, 70, 70)` + `1px rgb(88, 88, 88)` |
| Slider row height | `SLIDER_ROW_HEIGHT` | `20px` (margins `8, 0, 8, 0`, spacing `8px`) |
| Slider caption | `#sliderCaption` | Right-aligned, `74px` wide, `rgb(222, 222, 222)` |
| Slider value | `#sliderValue` | Right-aligned, `42px` wide, `rgb(218, 218, 218)` |
| Slider groove | `DevelopSlider` | `4px` tall recessed track, dark `1px` border `rgb(26, 26, 26)`, lower bevel `rgb(92, 92, 92)` |
| Slider ticks | `DevelopSlider` | 9 ticks above groove (`3px` at indices 0, 4, 8; `2px` at minors) |
| Slider pointer | `DevelopSlider` | Upward-pointing pentagon (`11px × 10px`), metallic gray gradient, `1px rgb(22, 22, 22)` outline |
| Scrollbar | `QScrollBar:vertical` | `9px` track `rgb(16, 16, 16)`, rounded `rgb(154, 154, 154)` handle, no step arrows |
| Filmstrip selection | `FilmstripWidget` | Trough `rgb(44, 44, 44)`, selected frame `rgb(190, 190, 190)` |

## Pure Geometry Helpers (Unit-Tested at >=95% Coverage)

`src/ui/widgets/slider_geometry.py` (pure Python, no Qt imports beyond or pure tuples so it is 100% deterministic):
- `value_ratio(value: int, minimum: int, maximum: int) -> float`
- `handle_center_x(ratio: float, left: int, right: int) -> int`
- `tick_positions(left: int, right: int, count: int = 9) -> tuple[tuple[int, bool], ...]`
- `pointer_polygon(center_x: int, top_y: int) -> tuple[tuple[int, int], ...]`
- `format_slider_value(title: str, value: int, minimum: int) -> str`
