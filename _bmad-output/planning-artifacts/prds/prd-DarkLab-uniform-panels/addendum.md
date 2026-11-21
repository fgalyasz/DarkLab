# Addendum — Cost-effective implementation blueprint

## Target files

- `src/ui/widgets/collapsible_section.py` — objectName, rounded shell, header radius on expand/collapse, PanelColumn spacing
- `src/ui/themes.py` — `#panelHeader` / `#collapsibleSection` radii
- `src/ui/develop_sections.py` — `crop_panel` without `_group("Crop")`
- `src/ui/panels/develop_panel.py` — tool stack spacing
- `tests/test_classic_density.py` — nesting + radius asserts
- `CHANGELOG.md`

## Tests

- `test_crop_panel_has_no_inner_crop_group`
- `test_develop_sections_do_not_nest_same_title`
- `test_collapsible_section_stylesheet_uses_panel_corner_radius`
