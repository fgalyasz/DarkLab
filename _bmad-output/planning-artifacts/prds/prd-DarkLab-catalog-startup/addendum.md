# Addendum: Catalog startup

## Stored keys

The domain dictionary uses `startup_mode`, `catalog_path`, and `fixed_catalog`.

The config file uses `catalog.startup_mode`, `catalog.path`, and `catalog.fixed_path`. The window translates between them. `src/catalog` does not read the config file and does not import Qt.

## Launch result

`plan_startup` returns one of:

- `ask` and no path — show Select Catalog before the workspace
- `open` and a path — that file exists

There is no `none` result. A launch that cannot open a file must ask. `require_catalog` returns the chooser's path, or nothing when the Photographer quits. Nothing means the process exits before `show()`.

## Rejected

- Making ask the default. It would change every current install.
- Clearing the pin when Startup Mode changes. The Photographer would have to browse again to return to fixed.
