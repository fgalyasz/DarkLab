# Addendum: Catalog startup

## Stored keys

The domain dictionary uses `startup_mode`, `catalog_path`, and `fixed_catalog`.

The config file uses `catalog.startup_mode`, `catalog.path`, and `catalog.fixed_path`. The window translates between them. `src/catalog` does not read the config file and does not import Qt.

## Launch result

`plan_startup` returns one of:

- `ask` and no path — show the Open Catalog window
- `open` and a path — that file exists
- `none` and no path — recent mode has nothing to open; leave the window without a Catalog

## Rejected

- Making ask the default. It would change every current install.
- Clearing the pin when Startup Mode changes. The Photographer would have to browse again to return to fixed.
