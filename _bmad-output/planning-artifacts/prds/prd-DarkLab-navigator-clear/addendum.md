# Addendum — Navigator clears on removal

`_show_paths` calls `_clear_selection_panels`. That paints an empty Navigator. `_show_pixmap` replaces a previous pixmap with an empty one before setting the empty-state text.
