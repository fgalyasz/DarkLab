from __future__ import annotations

CURRENT_SCHEMA = 2

META_TABLE = "CREATE TABLE IF NOT EXISTS catalog_meta (key TEXT PRIMARY KEY, value TEXT)"
META_ROW = f"INSERT OR IGNORE INTO catalog_meta (key, value) VALUES ('schema', '{CURRENT_SCHEMA}')"
PHOTO_TABLE = (
    "CREATE TABLE IF NOT EXISTS photos "
    "(id INTEGER PRIMARY KEY, original_path TEXT, content_hash TEXT)"
)
ADD_HASH = "ALTER TABLE photos ADD COLUMN content_hash TEXT"
ADD_SETTINGS = "ALTER TABLE photos ADD COLUMN develop_settings TEXT"
ADD_RATING = "ALTER TABLE photos ADD COLUMN rating TEXT"
ADD_PICK = "ALTER TABLE photos ADD COLUMN pick TEXT"
ADD_COLOR = "ALTER TABLE photos ADD COLUMN color TEXT"
ADD_CAPTURE = "ALTER TABLE photos ADD COLUMN capture_time REAL"
FOLDERS_TABLE = (
    "CREATE TABLE IF NOT EXISTS folders "
    "(id INTEGER PRIMARY KEY, folder_path TEXT NOT NULL UNIQUE)"
)
SCHEMA_QUERY = "SELECT value FROM catalog_meta WHERE key = 'schema'"
STORE_SCHEMA = "UPDATE catalog_meta SET value = ? WHERE key = 'schema'"
PHOTO_COLUMNS_QUERY = "PRAGMA table_info(photos)"
PHOTO_COLUMN_STATEMENTS = {
    "content_hash": ADD_HASH,
    "develop_settings": ADD_SETTINGS,
    "rating": ADD_RATING,
    "pick": ADD_PICK,
    "color": ADD_COLOR,
    "capture_time": ADD_CAPTURE,
}

CATALOG_INDEXES = {
    "idx_photos_content_hash": (
        "CREATE INDEX IF NOT EXISTS idx_photos_content_hash ON photos (content_hash)"
    ),
    "idx_photos_original_path": (
        "CREATE INDEX IF NOT EXISTS idx_photos_original_path ON photos (original_path)"
    ),
    "idx_photos_pick_rating": (
        "CREATE INDEX IF NOT EXISTS idx_photos_pick_rating ON photos (pick, rating)"
    ),
}
INDEX_NAMES_QUERY = "SELECT name FROM sqlite_master WHERE type = 'index'"
