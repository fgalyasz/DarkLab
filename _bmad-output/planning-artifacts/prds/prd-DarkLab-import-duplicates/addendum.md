# Addendum — Skip duplicates

`photos.content_hash` is nullable. New catalogs create the column. An older `photos` table gains it with `ALTER TABLE`, and a duplicate-column error is ignored.

`src/catalog/file_hash.py` hashes a file in 1 MiB chunks. `src/catalog/photos.py` inserts the hash with the Photo and fills null hashes before a scan. `src/importing/originals.py` skips when the path or the hash is already stored. `allow_duplicate` inserts a second Photo only for a different path.

The import dialog checkbox is off by default. Add passes it to `import_originals`. Copy and Move call `is_duplicate` on the source and leave that file in place when the hash is already known.
