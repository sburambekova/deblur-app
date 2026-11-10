from fastapi import APIRouter, HTTPException, Response, UploadFile

from app.schemas.jobs import JobOut
from app.schemas.params import DeblurParams
from app.schemas.photos import PhotoOut

router = APIRouter(prefix="/photos", tags=["photos"])


@router.post("", status_code=201)
def upload_photo(file: UploadFile) -> PhotoOut:
    raise HTTPException(501, "Not implemented yet")


@router.get("/{photo_id}")
def get_photo(photo_id: str) -> PhotoOut:
    raise HTTPException(501, "Not implemented yet")


@router.post(
    "/{photo_id}/preview",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}}}},
    description="Fast JPEG preview at preview size. Always uses Tikhonov, whatever `method` is: "
    "TV and R-L are too slow to follow a slider.",
)
def preview_photo(photo_id: str, params: DeblurParams) -> Response:
    raise HTTPException(501, "Not implemented yet")


@router.post("/{photo_id}/render", status_code=202)
def render_photo(photo_id: str, params: DeblurParams) -> JobOut:
    raise HTTPException(501, "Not implemented yet")


@router.post("/{photo_id}/estimate", description="Automatic kernel estimation, planned for later.")
def estimate_kernel(photo_id: str) -> None:
    raise HTTPException(501, "Not implemented yet")
