# Changelog

## Unreleased

- Library can remove index images from the catalog. The choice is to delete only the index image, or to delete the original file from disk as well.
- The Import side panel stays within its width. Long names and the metadata note wrap instead of opening a horizontal scrollbar.
- Import separates File Renaming, Metadata, and Destination into shaded blocks. Destination keeps its folder presets. The top bar, the source, the grid, and the bottom bar are separate bands.
- Import keeps Copy, Move, and Add in one row. Assisted Culling sits apart from that choice. The Add caption appears only while Add is selected.
- Import skips a photograph whose contents are already in the catalog. The same file is never added twice. "Import duplicates as new photos" records a second copy at a different path. A skip does not change the existing photograph and does not copy or move the file.
- Import shows the selected count and size, and the commit button stays off until something is selected. Copy leaves the originals in place. Move removes an original only after the copy matches its size.
- Importing photographs writes an index image into the open catalog, and the Library grid shows those images when the import dialog closes.
- A new catalog opens with an empty Library. The grid lists that catalog's index images, and it stays empty until some exist.
- A catalog is a folder. It records imported folder paths, stores index images, and keeps that catalog's settings. Originals stay on disk. Which catalog opens at launch stays outside the folder.
- The workspace opens only after a catalog is current. Select Catalog offers Open and New; Quit exits.
- Catalog Settings chooses the catalog at launch: always ask, the most recent catalog, or one pinned catalog. Opening another catalog does not change the pin.
- File → New Catalog creates a catalog, and the next launch reopens the last one. A display below 1920×1080 no longer blocks startup.
- Added the module shell: Library browser, Develop panel, and empty Map, Book, Slideshow, Print, and Web modules. Import can summarize a selection before a catalog exists.
- Published the product baseline: Classic workflow parity, a PRD, architecture, and an epic breakdown. The first milestone is one shoot from import to JPEG export. Adobe catalog compatibility and pixel-identical rendering are explicitly out.
