from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: str
    width: int
    height: int
    preview_width: int
    preview_height: int
    full_url: str
    preview_url: str
    spectrum_url: str
    created_at: str
