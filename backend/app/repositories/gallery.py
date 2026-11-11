"""The gallery_items table: render results the user decided to keep."""

import json
import sqlite3
from datetime import UTC, datetime

# Each item is read together with its job: the job knows the photo and the parameters.
SELECT_ITEMS = (
    "SELECT g.id, g.job_id, j.photo_id, g.caption, j.params, g.created_at "
    "FROM gallery_items AS g JOIN jobs AS j ON j.id = g.job_id"
)


def to_item(row: sqlite3.Row) -> dict:
    return dict(row, params=json.loads(row["params"]))


class GalleryRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, item_id: str, job_id: str, caption: str | None) -> None:
        self.conn.execute(
            "INSERT INTO gallery_items (id, job_id, caption, created_at) VALUES (?, ?, ?, ?)",
            (item_id, job_id, caption, datetime.now(UTC).isoformat()),
        )
        self.conn.commit()

    def list(self) -> list[dict]:
        """Newest first."""
        # rowid (insertion order) breaks ties between items created in the same microsecond.
        rows = self.conn.execute(
            SELECT_ITEMS + " ORDER BY g.created_at DESC, g.rowid DESC"
        ).fetchall()
        return [to_item(row) for row in rows]

    def get(self, item_id: str) -> dict | None:
        row = self.conn.execute(SELECT_ITEMS + " WHERE g.id = ?", (item_id,)).fetchone()
        return to_item(row) if row else None

    def delete(self, item_id: str) -> bool:
        """Delete one item; False if there was no such item."""
        cursor = self.conn.execute("DELETE FROM gallery_items WHERE id = ?", (item_id,))
        self.conn.commit()
        return cursor.rowcount > 0
