from fastapi import APIRouter, HTTPException

from app.schemas.jobs import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}")
def get_job(job_id: str) -> JobOut:
    raise HTTPException(501, "Not implemented yet")
