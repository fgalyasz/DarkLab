# Addendum — Library grid

`list_index_images` returns `previews/{photo_id}.jpg` files whose id is a positive integer, sorted by that id. Other files in `previews/` are ignored. A missing preview directory, including a legacy single-file Catalog, returns an empty list.

The Library and Develop panels call `show_catalog` when the open Catalog changes. They do not read `library.catalog_paths`.
