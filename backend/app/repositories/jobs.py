"""The jobs table: render jobs and their status (queued -> running -> done or failed)."""

import json
import sqlite3
from datetime import UTC, datetime


def now() -> str:
    return datetime.now(UTC).isoformat()


class JobRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    def create(self, job_id: str, photo_id: str, params: dict) -> None:
        self.conn.execute(
            "INSERT INTO jobs (id, photo_id, status, params, created_at) "
            "VALUES (?, ?, 'queued', ?, ?)",
            (job_id, photo_id, json.dumps(params), now()),
        )
        # Without commit the render thread, which has its own connection, would not find the job.
        self.conn.commit()

    def get(self, job_id: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        return dict(row, params=json.loads(row["params"]))

    def ids_for_photo(self, photo_id: str) -> list[str]:
        rows = self.conn.execute("SELECT id FROM jobs WHERE photo_id = ?", (photo_id,))
        return [row["id"] for row in rows]

    def delete_for_photo(self, photo_id: str) -> None:
        self.conn.execute("DELETE FROM jobs WHERE photo_id = ?", (photo_id,))
        self.conn.commit()

    def mark_running(self, job_id: str) -> None:
        self.conn.execute(
            "UPDATE jobs SET status = 'running', started_at = ? WHERE id = ?", (now(), job_id)
        )
        self.conn.commit()

    def mark_done(self, job_id: str, seconds: float) -> None:
        self.conn.execute(
            "UPDATE jobs SET status = 'done', finished_at = ?, seconds = ? WHERE id = ?",
            (now(), seconds, job_id),
        )
        self.conn.commit()

    def mark_failed(self, job_id: str, error: str) -> None:
        self.conn.execute(
            "UPDATE jobs SET status = 'failed', finished_at = ?, error = ? WHERE id = ?",
            (now(), error, job_id),
        )
        self.conn.commit()

    def fail_unfinished(self) -> None:
        """Fail every queued or running job: after a restart nobody will run them."""
        self.conn.execute(
            "UPDATE jobs SET status = 'failed', finished_at = ?, error = 'server restarted' "
            "WHERE status IN ('queued', 'running')",
            (now(),),
        )
        self.conn.commit()
