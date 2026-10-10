# Addendum — Catalog package

Product requirements are in `prd.md`. This note is the layout.

## Folder

```text
Name.darklab/
  catalog.sqlite
  previews/
  settings.json
```

`catalog.sqlite` is the only database. `previews/` holds index images named `{photo_id}.jpg`. `settings.json` is a JSON object of string values. Keys the application does not know yet are still stored.

A Catalog created earlier as a single `.darklab` file has no folder beside it. Open still accepts that file. New Catalogs do not use that shape.

## What is not in the folder

Startup Mode, `catalog.path`, and `catalog.fixed_path` stay in the application config. `src/catalog` does not read that config and does not import Qt.

Original files are not copied into the folder by recording a folder path.

## Domain

- `src/catalog/locations.py` — paths inside the folder.
- `src/catalog/database.py` — create, open, schema.
- `src/catalog/folders.py` — imported folder paths.
- `src/catalog/index_images.py` — preview files.
- `src/catalog/catalog_settings.py` — the JSON object.

The Open dialog selects the folder. New Catalog still asks for a name, then creates the folder.
