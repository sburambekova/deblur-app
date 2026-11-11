from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_render_service
from app.schemas.jobs import JobOut
from app.services.render import RenderService

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", description="`result_url` is set only when `status` is `done`.")
def get_job(job_id: str, service: Annotated[RenderService, Depends(get_render_service)]) -> JobOut:
    return service.get(job_id)
