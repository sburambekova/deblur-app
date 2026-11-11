from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile

from app.deps import get_photo_service, get_render_service
from app.schemas.jobs import JobOut
from app.schemas.params import DeblurParams
from app.schemas.photos import PhotoOut
from app.services.photos import PhotoService
from app.services.render import RenderService

router = APIRouter(prefix="/photos", tags=["photos"])

Photos = Annotated[PhotoService, Depends(get_photo_service)]
Renders = Annotated[RenderService, Depends(get_render_service)]

NO_PHOTO = {404: {"description": "No such photo"}}


@router.post(
    "",
    status_code=201,
    summary="Upload a photo",
    description="JPEG, PNG, HEIC and other formats Pillow can read. The photo is rotated by EXIF "
    "and saved as full.png (larger side up to 1600 px), preview.png (512 px) and spectrum.png.",
    responses={
        400: {"description": "Not an image, a broken file, or smaller than 64 px on a side"},
        413: {"description": "File larger than the limit (15 MB by default)"},
    },
)
def upload_photo(file: UploadFile, service: Photos) -> PhotoOut:
    # file.read() is async and would return a coroutine in a plain def endpoint.
    # One byte over the limit is enough to know the file is too large.
    data = file.file.read(service.max_bytes + 1)
    return service.upload(data)


@router.get("/{photo_id}", summary="Get a photo", responses=NO_PHOTO)
def get_photo(photo_id: str, service: Photos) -> PhotoOut:
    return service.get(photo_id)


@router.post(
    "/{photo_id}/preview",
    summary="Live preview",
    response_class=Response,
    responses={200: {"content": {"image/jpeg": {}}}, **NO_PHOTO},
    description="Fast JPEG preview at preview size. Always uses Tikhonov, whatever `method` is: "
    "TV and R-L are too slow to follow a slider. The `X-Compute-Ms` header gives the server time.",
)
def preview_photo(photo_id: str, params: DeblurParams, service: Photos) -> Response:
    jpeg, ms = service.preview(photo_id, params)
    return Response(content=jpeg, media_type="image/jpeg", headers={"X-Compute-Ms": f"{ms:.1f}"})


@router.post(
    "/{photo_id}/render",
    status_code=202,
    summary="Start a full-size render",
    description="Start a full-size render in the background. Poll GET /api/jobs/{job_id} "
    "until `status` is `done` or `failed`. Lengths are in preview pixels, as for /preview.",
    responses={**NO_PHOTO, 429: {"description": "Too many jobs in the queue, try again later"}},
)
def render_photo(photo_id: str, params: DeblurParams, service: Renders) -> JobOut:
    return service.submit(photo_id, params)


@router.post(
    "/{photo_id}/estimate",
    summary="Estimate the blur kernel (not implemented yet)",
    description="Automatic kernel estimation, planned for later.",
    responses={501: {"description": "Not implemented yet"}},
)
def estimate_kernel(photo_id: str) -> None:
    raise HTTPException(501, "Not implemented yet")
