# Addendum — Cost-effective implementation blueprint

## Target files

- `src/ui/widgets/filmstrip_widget.py`
- `tests/test_large_catalog.py` (FilmstripModelTests)
- `tests/test_develop_filmstrip.py` (layout height assert)
- `CHANGELOG.md`

## Contracts

```python
CELL_SIZE = QSize(108, 88)
ICON_SIZE = QSize(96, 72)
STRIP_HEIGHT = 110

# FilmstripModel.data:
# DisplayRole -> ""
# ToolTipRole -> path.name
# DecorationRole / UserRole unchanged

# FilmstripWidget.__init__:
# setGridSize(CELL_SIZE); setIconSize(ICON_SIZE); setFixedHeight(STRIP_HEIGHT)
```

## Tests

- DisplayRole empty string; ToolTipRole equals file name.
- `iconSize().height() >= 56`, `gridSize().height() >= iconSize().height()`, `height() >= gridSize().height()`.
