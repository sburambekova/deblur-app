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

    def list_old_not_in_gallery(self, before: str) -> list[str]:
        """IDs of photos created before `before` (ISO time) that no gallery item uses."""
        rows = self.conn.execute(
            "SELECT id FROM photos WHERE created_at < ? AND id NOT IN ("
            "  SELECT j.photo_id FROM gallery_items AS g JOIN jobs AS j ON j.id = g.job_id"
            ")",
            (before,),
        ).fetchall()
        return [row["id"] for row in rows]

    def delete(self, photo_id: str) -> None:
        self.conn.execute("DELETE FROM photos WHERE id = ?", (photo_id,))
        self.conn.commit()
