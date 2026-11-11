"""FastAPI application: settings, CORS, error handlers, routers, static files and startup."""

import logging
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, closing

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import db
from app.config import Settings
from app.errors import (
    ConflictError,
    InvalidInputError,
    NotFoundError,
    TooLargeError,
    TooManyJobsError,
)
from app.repositories.jobs import JobRepository
from app.routers import gallery, health, jobs, photos
from app.services.photos import delete_old_photos

ERROR_STATUS = {
    NotFoundError: 404,
    InvalidInputError: 400,
    ConflictError: 409,
    TooLargeError: 413,
    TooManyJobsError: 429,
}


def error_response(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=ERROR_STATUS[type(exc)], content={"detail": str(exc)})


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    # uvicorn sets up only its own loggers; this makes the app's log lines visible.
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    (settings.files_dir / "photos").mkdir(parents=True, exist_ok=True)
    (settings.files_dir / "results").mkdir(parents=True, exist_ok=True)
    with closing(db.connect(settings.db_path)) as conn:
        db.init_schema(conn)
        JobRepository(conn).fail_unfinished()
        delete_old_photos(settings, conn)
    # One worker: a render already uses all cores (scipy FFT with workers=-1), so two renders
    # at once would not finish sooner, they would only slow each other down.
    app.state.executor = ThreadPoolExecutor(max_workers=1)
    yield
    app.state.executor.shutdown(wait=False, cancel_futures=True)


# A factory instead of a global app, so tests can build an app on a temporary data folder.
def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Deblur API", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        # Without this the browser hides the X-Compute-Ms header of /preview from the frontend.
        expose_headers=["X-Compute-Ms"],
    )
    for error in ERROR_STATUS:
        app.add_exception_handler(error, error_response)
    app.include_router(health.router, prefix="/api")
    app.include_router(photos.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    app.include_router(gallery.router, prefix="/api")
    # Only files/ is served; the database lies next to it in data_dir and stays private.
    # check_dir=False: the folder is created by lifespan, which runs after create_app.
    # StaticFiles still checks it on the first request.
    app.mount("/files", StaticFiles(directory=settings.files_dir, check_dir=False), name="files")
    return app


app = create_app()
