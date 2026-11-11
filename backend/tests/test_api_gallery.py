from contextlib import closing

from fastapi.testclient import TestClient

from app import db
from app.repositories.jobs import JobRepository
from app.schemas.params import DeblurParams
from tests.test_api_render import render, upload, wait_for


def done_job(client: TestClient, params: dict) -> dict:
    photo = upload(client, 120, 90)
    job = wait_for(client, render(client, photo["id"], params)["id"])
    assert job["status"] == "done"
    return job


def add(client: TestClient, job_id: str, caption: str | None = None):
    return client.post("/api/gallery", json={"job_id": job_id, "caption": caption})


def test_add_list_delete(client):
    first = done_job(client, {"method": "tikhonov", "length": 9})
    second = done_job(client, {"method": "rl", "iters": 5})

    response = add(client, first["id"], "my cat")
    assert response.status_code == 201
    item = response.json()
    assert item["job_id"] == first["id"]
    assert item["photo_id"] == first["photo_id"]
    assert item["caption"] == "my cat"
    assert item["params"] == first["params"]
    assert item["before_url"] == f"/files/photos/{first['photo_id']}/full.png"
    assert item["after_url"] == first["result_url"]
    assert client.get(item["before_url"]).status_code == 200
    assert client.get(item["after_url"]).status_code == 200

    newer = add(client, second["id"]).json()
    assert newer["caption"] is None
    items = client.get("/api/gallery").json()
    assert [i["id"] for i in items] == [newer["id"], item["id"]]

    response = client.delete(f"/api/gallery/{item['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert [i["id"] for i in client.get("/api/gallery").json()] == [newer["id"]]


def test_empty_gallery(client):
    response = client.get("/api/gallery")
    assert response.status_code == 200
    assert response.json() == []


def test_unfinished_job_is_409(client, tmp_path):
    # A queued job written straight to the database, so it cannot finish during the test.
    with closing(db.connect(tmp_path / "deblur.sqlite3")) as conn:
        JobRepository(conn).create("queued-job", "some-photo", DeblurParams().model_dump())
    response = add(client, "queued-job")
    assert response.status_code == 409
    assert response.json() == {"detail": "Job is not done yet"}


def test_unknown_job_is_404(client):
    response = add(client, "does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}


def test_delete_unknown_item_is_404(client):
    response = client.delete("/api/gallery/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Gallery item not found"}


def test_long_caption_is_422(client):
    assert add(client, "any-job", "x" * 121).status_code == 422
