# Addendum — Import summary

`src/importing/transfer.py` copies and moves one file. `src/importing/discover.py` lists images. `ImageDiscoveryThread.run` calls `discover_images` on the worker thread.

The summary passes `byte_total(selected)` into the existing status text. The commit button is enabled only when the selection is not empty and an import is not already running.

Add records files one at a time and sets the status to `Added done/total`.
