"""The photos table."""

import sqlite3


class PhotoRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, photo: dict) -> None:
        self.conn.execute(
            "INSERT INTO photos (id, width, height, preview_width, preview_height, created_at) "
            "VALUES (:id, :width, :height, :preview_width, :preview_height, :created_at)",
            photo,
        )
        # Without commit other connections (e.g. a render thread) would not see the new row.
        self.conn.commit()

    def get(self, photo_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM photos WHERE id = ?", (photo_id,)).fetchone()
        return dict(row) if row else None
