"""Dependencies for Depends(): settings, a database connection per request, services."""

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request

from app import db
from app.config import Settings
from app.repositories.files import FileStorage
from app.repositories.jobs import JobRepository
from app.repositories.photos import PhotoRepository
from app.services.photos import PhotoService
from app.services.render import RenderService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_db(request: Request) -> Iterator[sqlite3.Connection]:
    conn = db.connect(get_settings(request).db_path)
    try:
        yield conn
    finally:
        conn.close()


def get_photo_service(
    settings: Annotated[Settings, Depends(get_settings)],
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> PhotoService:
    return PhotoService(settings, PhotoRepository(conn), FileStorage(settings.files_dir))


def get_render_service(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    conn: Annotated[sqlite3.Connection, Depends(get_db)],
) -> RenderService:
    return RenderService(
        settings,
        PhotoRepository(conn),
        JobRepository(conn),
        FileStorage(settings.files_dir),
        request.app.state.executor,
    )
