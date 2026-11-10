"""FastAPI application: settings, CORS, error handlers and routers."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings
from app.errors import ConflictError, InvalidInputError, NotFoundError
from app.routers import gallery, health, jobs, photos

ERROR_STATUS = {NotFoundError: 404, InvalidInputError: 400, ConflictError: 409}


def error_response(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=ERROR_STATUS[type(exc)], content={"detail": str(exc)})


# A factory instead of a global app, so tests can build an app on a temporary data folder.
def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Deblur API")
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
    return app


app = create_app()
