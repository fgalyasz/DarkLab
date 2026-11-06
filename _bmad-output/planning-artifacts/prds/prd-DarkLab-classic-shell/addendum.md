# Classic shell checklist

| Area | Expectation | Test |
| --- | --- | --- |
| Module bar | Library, Develop, Map, Book, Slideshow, Print, Web | `tests/test_lightroom_shell.py` `test_main_window_modules` |
| Library | Filmstrip under the main view | `tests/test_classic_shell.py` |
| Library | Left and right column sections in Classic roles | `tests/test_classic_shell.py` |
| Develop | Right column order Histogram, tool strip, Basic to Calibration | `tests/test_classic_shell.py` |
| Develop | Left column Navigator, Presets, Snapshots, History, Collections | `tests/test_classic_shell.py` |
| Import | Source, grid, options bands; Copy / Move / Add one row; no side scrollbar | `tests/test_classic_shell.py` |
| Contrast | Body labels at least 4.5:1 | `tests/test_classic_shell.py`, `tests/test_cull_filter.py` |
