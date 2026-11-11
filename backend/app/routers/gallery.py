from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_gallery_service
from app.schemas.gallery import GalleryItemCreate, GalleryItemOut
from app.services.gallery import GalleryService

router = APIRouter(prefix="/gallery", tags=["gallery"])

Gallery = Annotated[GalleryService, Depends(get_gallery_service)]


@router.get("", summary="List the gallery", description="Saved before/after pairs, newest first.")
def list_gallery(service: Gallery) -> list[GalleryItemOut]:
    return service.list()


@router.post(
    "",
    status_code=201,
    summary="Add a render to the gallery",
    description="Save a finished render. The same job may be added more than once.",
    responses={
        404: {"description": "No such job"},
        409: {"description": "The job is not done yet"},
    },
)
def add_to_gallery(item: GalleryItemCreate, service: Gallery) -> GalleryItemOut:
    return service.add(item.job_id, item.caption)


@router.delete(
    "/{item_id}",
    status_code=204,
    summary="Remove from the gallery",
    description="Removes only the gallery entry; the photo and the result stay.",
    responses={404: {"description": "No such gallery item"}},
)
def delete_from_gallery(item_id: str, service: Gallery) -> None:
    service.delete(item_id)
