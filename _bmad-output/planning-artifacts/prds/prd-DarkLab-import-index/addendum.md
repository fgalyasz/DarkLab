# Addendum — Import index images

`import_originals` ensures the schema, inserts a Photo when the path is new, records the parent folder, and writes `previews/{photo_id}.jpg`.

For a Catalog folder, that directory is `Name.darklab/previews/`. For a single-file Catalog, it is `Name.darklab.previews/`.

The index image is a JPEG whose long edge is at most 360 pixels. JPEG and PNG are read with Pillow. Other files try the embedded RAW thumbnail. A file that cannot be read is logged and skipped.

The Import dialog receives the open Catalog through `bind_catalog`. When the dialog closes, the Library and Develop panels reload `list_index_images`.
