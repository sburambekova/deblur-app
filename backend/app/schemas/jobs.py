from typing import Literal

from pydantic import BaseModel

from app.schemas.params import DeblurParams


class JobOut(BaseModel):
    id: str
    photo_id: str
    status: Literal["queued", "running", "done", "failed"]
    params: DeblurParams
    result_url: str | None
    error: str | None
    created_at: str
    started_at: str | None
    finished_at: str | None
    seconds: float | None
