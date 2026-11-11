"""SQLite connection and schema. Plain sqlite3, no ORM: three small tables."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS photos (
    id TEXT PRIMARY KEY,
    width INT,
    height INT,
    preview_width INT,
    preview_height INT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    photo_id TEXT,
    status TEXT,
    params TEXT,  -- DeblurParams as a JSON string
    error TEXT,
    created_at TEXT,
    started_at TEXT,
    finished_at TEXT,
    seconds REAL
);
CREATE TABLE IF NOT EXISTS gallery_items (
    id TEXT PRIMARY KEY,
    job_id TEXT,
    caption TEXT,
    created_at TEXT
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    # FastAPI may open the connection in one worker thread and use it in another, which sqlite3
    # refuses by default. Each request gets its own connection, so it is never shared.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
