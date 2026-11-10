from pydantic import BaseModel, Field

from app.schemas.params import DeblurParams


class GalleryItemCreate(BaseModel):
    job_id: str
    caption: str | None = Field(None, max_length=120)


class GalleryItemOut(BaseModel):
    id: str
    job_id: str
    photo_id: str
    before_url: str
    after_url: str
    caption: str | None
    params: DeblurParams
    created_at: str
