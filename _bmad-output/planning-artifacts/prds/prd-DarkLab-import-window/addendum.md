# Addendum — A usable Import window

`_render_import_sections` builds only the Destination section. `_show_destination_section` shows it for Copy and Move. `_write_destination` stores that folder as the Default destination preset with `organize_mode` `one_folder`, which is what Copy and Move already read.

The preset, rename, and metadata builders remain in `import_dialog.py` and are not placed on the window.
