import time
from contextlib import closing
from io import BytesIO

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import db
from app.config import Settings
from app.engine import kernels, pipeline
from app.main import create_app
from app.repositories.jobs import JobRepository
from app.schemas.params import DeblurParams


def upload(client: TestClient, width: int, height: int) -> dict:
    pixels = np.random.default_rng(0).integers(0, 256, (height, width, 3), dtype=np.uint8)
    buf = BytesIO()
    Image.fromarray(pixels).save(buf, "PNG")
    response = client.post("/api/photos", files={"file": ("photo.png", buf.getvalue())})
    assert response.status_code == 201
    return response.json()


def render(client: TestClient, photo_id: str, params: dict) -> dict:
    response = client.post(f"/api/photos/{photo_id}/render", json=params)
    assert response.status_code == 202
    return response.json()


def wait_for(client: TestClient, job_id: str, timeout: float = 20) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = client.get(f"/api/jobs/{job_id}").json()
        if job["status"] in ("done", "failed"):
            return job
        time.sleep(0.05)
    raise AssertionError(f"job {job_id} did not finish in {timeout} s")


def test_render_job_finishes(client):
    photo = upload(client, 120, 90)
    job = render(client, photo["id"], {"method": "rl", "iters": 5})
    # The worker may already have picked the job up by the time the response is built.
    assert job["status"] in ("queued", "running")
    assert job["result_url"] is None
    job = wait_for(client, job["id"])
    assert job["status"] == "done"
    assert job["error"] is None
    assert job["seconds"] > 0
    assert job["started_at"] and job["finished_at"]
    result = client.get(job["result_url"])
    assert result.status_code == 200
    assert Image.open(BytesIO(result.content)).size == (photo["width"], photo["height"])


@pytest.mark.parametrize("method", ["tikhonov", "tv", "rl"])
def test_every_method_finishes(client, method):
    photo = upload(client, 120, 90)
    job = wait_for(client, render(client, photo["id"], {"method": method, "iters": 5})["id"])
    assert job["status"] == "done"
    assert job["params"]["method"] == method


def test_unknown_photo_is_404(client):
    response = client.post("/api/photos/does-not-exist/render", json={})
    assert response.status_code == 404
    assert response.json() == {"detail": "Photo not found"}


def test_unknown_job_is_404(client):
    response = client.get("/api/jobs/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_params_are_scaled_to_full_size(client, monkeypatch):
    calls = []

    def recording_make_psf(kernel, length, angle, radius):
        calls.append((kernel, length, angle, radius))
        return kernels.motion_psf(1, 0)

    monkeypatch.setattr(kernels, "make_psf", recording_make_psf)
    # Full 1024 x 768, preview 512 x 384: the full photo is twice as large.
    photo = upload(client, 1024, 768)
    params = {"length": 15, "angle": 30, "radius": 3, "method": "tikhonov"}
    job = wait_for(client, render(client, photo["id"], params)["id"])
    assert job["status"] == "done"
    assert calls == [("motion", 30, 30, 6)]
    # The job keeps the parameters as sent, in preview pixels.
    assert job["params"]["length"] == 15


def test_error_in_render_fails_the_job(client, monkeypatch):
    def broken_deblur(*args, **kwargs):
        raise RuntimeError("engine exploded")

    monkeypatch.setattr(pipeline, "deblur", broken_deblur)
    photo = upload(client, 120, 90)
    job = wait_for(client, render(client, photo["id"], {})["id"])
    assert job["status"] == "failed"
    assert job["error"] == "engine exploded"
    assert job["result_url"] is None


def test_unfinished_jobs_fail_after_restart(tmp_path):
    settings = Settings(data_dir=tmp_path)
    # A job that was queued when the server stopped.
    with TestClient(create_app(settings)), closing(db.connect(settings.db_path)) as conn:
        JobRepository(conn).create("left-behind", "some-photo", DeblurParams().model_dump())
    with TestClient(create_app(settings)) as client:
        job = client.get("/api/jobs/left-behind").json()
    assert (job["status"], job["error"]) == ("failed", "server restarted")


def test_render_logs_one_line(client, caplog):
    caplog.set_level("INFO", logger="app.services.render")
    photo = upload(client, 120, 90)
    job = wait_for(client, render(client, photo["id"], {"method": "rl", "iters": 5})["id"])
    lines = [r.getMessage() for r in caplog.records if r.name == "app.services.render"]
    assert len(lines) == 1
    assert job["id"] in lines[0] and "rl, 120x90" in lines[0]
