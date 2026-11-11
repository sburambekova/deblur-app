"""Dependencies for Depends(): settings and a database connection per request."""

import sqlite3
from collections.abc import Iterator

from fastapi import Request

from app import db
from app.config import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = db.connect(get_settings(request).db_path)
    try:
        yield conn
    finally:
        conn.close()
