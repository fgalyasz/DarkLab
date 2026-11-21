# Classic density checklist

| Surface | Cap | Check |
| --- | --- | --- |
| Body / control font | ≤ 11px | `Density.BODY_PX`, `tests/test_classic_density.py` |
| Panel header font | ≤ 11px | `Density.HEADER_PX` |
| Hint / secondary font | ≤ 10px | `Density.HINT_PX` |
| Module / placeholder title | ≤ 13px | `Density.TITLE_PX` |
| Module bar height | ≤ 30px | `Density.MODULE_BAR_HEIGHT` |
| Panel header height | ≤ 22px | `Density.PANEL_HEADER_HEIGHT` |
| Library filter strip | ≤ 28px | `LibraryBrowserPanel._filter_bar` |
| Library bottom tool strip | ≤ 32px | `LibraryBrowserPanel._build_toolbar` |
| Color wheel width | ≤ 86px | `ColorWheel` fixed width |
| Three grading wheels | fit in 280px column | `tests/test_classic_density.py` |
| SliderRow single line | no wrap at 280px | `tests/test_classic_density.py` |
| Body contrast | ≥ 4.5:1 | existing classic shell tests |

## Cost-Effective Implementation Blueprint

### Story A — Density tokens and theme

- Files: `src/ui/density.py` (new), `src/ui/themes.py`, `tests/test_classic_density.py`
- `Density` class with the constants above
- `StyleSheet.LIGHTROOM` uses `Density.BODY_PX` / `HEADER_PX` via f-string
- `DarkTheme.apply_theme` sets application font point size to `BODY_PX` mapped to points (11)

### Story B — Shell widgets

- Files: `src/ui/widgets/module_bar.py`, `src/ui/widgets/collapsible_section.py`, `src/ui/widgets/slider_row.py`, `src/ui/widgets/color_wheel.py`, `src/ui/panels/base_panel.py`, placeholder panels under `src/ui/panels/`
- Apply heights and fonts from `Density`
- SliderRow: caption min/max width, `ElideRight`, value min width 36
- ColorWheel: 84×100

### Story C — Library, Develop, Import chrome

- Files: `src/ui/panels/library_browser_panel.py`, `src/ui/panels/develop_panel.py`, `src/ui/dialogs/import_dialog.py` (font-size literals only)
- Filter/tool strip heights; metadata elide; develop info labels; import block titles ≤ 11px
