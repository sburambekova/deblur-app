"""Full-size render as a background job: the request returns at once, a worker thread deblurs."""

import logging
import sqlite3
import time
from concurrent.futures import Executor
from contextlib import closing
from uuid import uuid4

from app import db
from app.config import Settings
from app.engine import kernels, pipeline
from app.errors import NotFoundError, TooManyJobsError
from app.repositories.files import FileStorage
from app.repositories.jobs import JobRepository
from app.repositories.photos import PhotoRepository
from app.schemas.params import DeblurParams

logger = logging.getLogger(__name__)

RESULT_QUALITY = 92
# Only the parameters of the chosen method go to deblur.
METHOD_PARAMS = {"tikhonov": ("mu", "penalty"), "tv": ("lam",), "rl": ("iters",)}


class RenderService:
    def __init__(
        self,
        settings: Settings,
        photos: PhotoRepository,
        jobs: JobRepository,
        storage: FileStorage,
        executor: Executor,
    ) -> None:
        self.settings = settings
        self.photos = photos
        self.jobs = jobs
        self.storage = storage
        self.executor = executor

    def submit(self, photo_id: str, params: DeblurParams) -> dict:
        if self.photos.get(photo_id) is None:
            raise NotFoundError("Photo not found")
        # The running job is not counted: only jobs still waiting for the worker.
        if self.jobs.count_queued() >= self.settings.max_queued_jobs:
            raise TooManyJobsError("Too many jobs, try again later")
        job_id = uuid4().hex
        self.jobs.create(job_id, photo_id, params.model_dump())
        self.executor.submit(run_job, self.settings, job_id)
        return self.get(job_id)

    def get(self, job_id: str) -> dict:
        job = self.jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        done = job["status"] == "done"
        result_url = self.storage.url_for(self.storage.result_path(job_id)) if done else None
        return {**job, "result_url": result_url}


def run_job(settings: Settings, job_id: str) -> None:
    """Runs in the worker thread. The request's connection is closed by now, so open our own."""
    with closing(db.connect(settings.db_path)) as conn:
        jobs = JobRepository(conn)
        jobs.mark_running(job_id)
        try:
            seconds = render(settings, conn, job_id)
        # Any error must end up in the job, otherwise it would vanish with the thread.
        except Exception as exc:
            logger.exception("Render job %s failed", job_id)
            jobs.mark_failed(job_id, str(exc))
        else:
            jobs.mark_done(job_id, seconds)


def render(settings: Settings, conn: sqlite3.Connection, job_id: str) -> float:
    """Deblur the full-size photo of the job and save the result; returns seconds taken."""
    start = time.perf_counter()
    job = JobRepository(conn).get(job_id)
    photo = PhotoRepository(conn).get(job["photo_id"])
    storage = FileStorage(settings.files_dir)
    full = storage.read_rgb(storage.full_path(photo["id"]))
    # Parameters were chosen on the preview; scale them to the full-size photo.
    s = max(full.shape[:2]) / max(photo["preview_width"], photo["preview_height"])
    p = pipeline.scale_params(job["params"], s)
    psf = kernels.make_psf(p["kernel"], p["length"], p["angle"], p["radius"])
    method_params = {name: p[name] for name in METHOD_PARAMS[p["method"]]}
    out = pipeline.deblur(full, psf, p["method"], **method_params)
    storage.write_jpeg(storage.result_path(job_id), out, RESULT_QUALITY)
    seconds = time.perf_counter() - start
    h, w = full.shape[:2]
    logger.info("Render %s: %s, %dx%d, %.1f s", job_id, p["method"], w, h, seconds)
    return seconds
