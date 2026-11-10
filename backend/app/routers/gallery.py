from fastapi import APIRouter, HTTPException

from app.schemas.gallery import GalleryItemCreate, GalleryItemOut

router = APIRouter(prefix="/gallery", tags=["gallery"])


@router.get("")
def list_gallery() -> list[GalleryItemOut]:
    raise HTTPException(501, "Not implemented yet")


@router.post("", status_code=201)
def add_to_gallery(item: GalleryItemCreate) -> GalleryItemOut:
    raise HTTPException(501, "Not implemented yet")


@router.delete("/{item_id}", status_code=204)
def delete_from_gallery(item_id: str) -> None:
    raise HTTPException(501, "Not implemented yet")
