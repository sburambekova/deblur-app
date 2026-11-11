from contextlib import closing
from datetime import UTC, datetime, timedelta
from io import BytesIO

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app import db
from app.config import Settings
from app.main import create_app
from tests.test_api_render import render, wait_for


def image_bytes(
    width: int, height: int, fmt: str = "JPEG", orientation: int | None = None
) -> bytes:
    pixels = np.random.default_rng(0).integers(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(pixels)
    exif = Image.Exif()
    if orientation is not None:
        exif[0x0112] = orientation  # EXIF Orientation tag
    buf = BytesIO()
    img.save(buf, fmt, exif=exif)
    return buf.getvalue()


def upload(client: TestClient, data: bytes, name: str = "photo.jpg"):
    return client.post("/api/photos", files={"file": (name, data)})


def download_image(client: TestClient, url: str) -> Image.Image:
    response = client.get(url)
    assert response.status_code == 200
    return Image.open(BytesIO(response.content))


@pytest.mark.parametrize("fmt", ["JPEG", "PNG"])
def test_upload(client, fmt):
    response = upload(client, image_bytes(300, 200, fmt))
    assert response.status_code == 201
    photo = response.json()
    assert (photo["width"], photo["height"]) == (300, 200)
    assert (photo["preview_width"], photo["preview_height"]) == (300, 200)
    assert download_image(client, photo["full_url"]).size == (300, 200)
    assert download_image(client, photo["preview_url"]).size == (300, 200)
    spectrum = download_image(client, photo["spectrum_url"])
    assert (spectrum.size, spectrum.mode) == ((256, 256), "L")


def test_get_photo(client):
    photo = upload(client, image_bytes(300, 200)).json()
    response = client.get(f"/api/photos/{photo['id']}")
    assert response.status_code == 200
    assert response.json() == photo


def test_exif_rotation_swaps_sides(client):
    # Orientation 6: the camera was turned by 90 degrees, so the photo is shown upright as 200x300.
    photo = upload(client, image_bytes(300, 200, orientation=6)).json()
    assert (photo["width"], photo["height"]) == (200, 300)


def test_large_photo_is_resized(client):
    photo = upload(client, image_bytes(2000, 1500)).json()
    assert (photo["width"], photo["height"]) == (1600, 1200)
    assert (photo["preview_width"], photo["preview_height"]) == (512, 384)
    assert download_image(client, photo["full_url"]).size == (1600, 1200)
    assert download_image(client, photo["preview_url"]).size == (512, 384)


def test_text_file_is_rejected(client):
    response = upload(client, b"not an image at all", "notes.txt")
    assert response.status_code == 400
    assert response.json() == {"detail": "Not a valid image"}


def test_truncated_jpeg_is_rejected(client):
    truncated = image_bytes(800, 600)[:4096]
    # Pillow opens it fine, the error only shows up when the pixels are decoded.
    Image.open(BytesIO(truncated))
    response = upload(client, truncated)
    assert response.status_code == 400
    assert response.json() == {"detail": "Not a valid image"}


def test_narrow_image_is_rejected(client):
    response = upload(client, image_bytes(2000, 40))
    assert response.status_code == 400
    assert response.json() == {"detail": "Image is too small or too narrow"}


def test_too_large_file_is_rejected(tmp_path):
    app = create_app(Settings(data_dir=tmp_path, max_upload_mb=1))
    with TestClient(app) as client:
        response = upload(client, b"x" * (1024 * 1024 + 1))
    assert response.status_code == 413


def test_unknown_photo_is_404(client):
    response = client.get("/api/photos/does-not-exist")
    assert response.status_code == 404
    assert response.json() == {"detail": "Photo not found"}


def test_database_is_not_served(client, tmp_path):
    assert (tmp_path / "deblur.sqlite3").exists()
    # The test client turns /files/../x into /x itself; an encoded slash reaches StaticFiles.
    for url in ["/files/..%2fdeblur.sqlite3", "/deblur.sqlite3"]:
        assert client.get(url).status_code == 404


def test_old_photos_are_deleted_at_startup(tmp_path):
    settings = Settings(data_dir=tmp_path)
    with TestClient(create_app(settings)) as client:
        old, kept, fresh = (upload(client, image_bytes(120, 90)).json() for _ in range(3))
        old_job = wait_for(client, render(client, old["id"], {"method": "tikhonov"})["id"])
        kept_job = wait_for(client, render(client, kept["id"], {"method": "tikhonov"})["id"])
        assert client.post("/api/gallery", json={"job_id": kept_job["id"]}).status_code == 201

    # Pretend `old` and `kept` were uploaded two days ago; `kept` is in the gallery.
    two_days_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
    with closing(db.connect(settings.db_path)) as conn:
        conn.execute(
            "UPDATE photos SET created_at = ? WHERE id IN (?, ?)",
            (two_days_ago, old["id"], kept["id"]),
        )
        conn.commit()

    with TestClient(create_app(settings)) as client:
        assert client.get(f"/api/photos/{old['id']}").status_code == 404
        assert client.get(f"/api/jobs/{old_job['id']}").status_code == 404
        assert not (tmp_path / "files" / "photos" / old["id"]).exists()
        assert not (tmp_path / "files" / "results" / f"{old_job['id']}.jpg").exists()

        assert client.get(f"/api/photos/{kept['id']}").status_code == 200
        assert client.get(kept_job["result_url"]).status_code == 200
        assert len(client.get("/api/gallery").json()) == 1
        assert client.get(f"/api/photos/{fresh['id']}").status_code == 200
