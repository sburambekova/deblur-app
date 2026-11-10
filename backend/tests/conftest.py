from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    app = create_app(Settings(data_dir=tmp_path))
    # Inside `with` the app's lifespan runs, as on a real server.
    with TestClient(app) as client:
        yield client
