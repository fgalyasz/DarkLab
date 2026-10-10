# Addendum — Remove index images

`src/catalog/removal.py` deletes the index JPEG and the Photo row. When the Photographer also chooses the Original, that stored file is unlinked first. If the unlink fails, the Photo and the index image stay.

The Library toolbar button is Remove. Delete and Backspace on the grid open the same dialog. The dialog buttons are "Delete index image only", "Also delete the original from disk", and Cancel.
