from io import BytesIO

import numpy as np
from fastapi.testclient import TestClient
from PIL import Image

from app.engine.kernels import make_psf
from tests.helpers import blurred_case, load_test_image, psnr


def png_bytes(rgb: np.ndarray) -> bytes:
    buf = BytesIO()
    Image.fromarray(np.round(rgb * 255).astype(np.uint8)).save(buf, "PNG")
    return buf.getvalue()


def upload(client: TestClient, rgb: np.ndarray) -> dict:
    response = client.post("/api/photos", files={"file": ("photo.png", png_bytes(rgb))})
    assert response.status_code == 201
    return response.json()


def preview(client: TestClient, photo_id: str, params: dict):
    return client.post(f"/api/photos/{photo_id}/preview", json=params)


def test_preview_is_a_jpeg_of_preview_size(client):
    rgb = np.random.default_rng(0).random((200, 300, 3))
    photo = upload(client, rgb)
    response = preview(client, photo["id"], {"length": 9, "angle": 30})
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert float(response.headers["x-compute-ms"]) > 0
    img = Image.open(BytesIO(response.content))
    assert (img.format, img.size) == ("JPEG", (300, 200))


def test_preview_ignores_method(client):
    photo = upload(client, np.random.default_rng(0).random((100, 100, 3)))
    tikhonov = preview(client, photo["id"], {"method": "tikhonov"})
    rl = preview(client, photo["id"], {"method": "rl"})
    assert tikhonov.content == rl.content


def test_bad_params_are_422(client):
    photo = upload(client, np.random.default_rng(0).random((100, 100, 3)))
    assert preview(client, photo["id"], {"kernel": "gauss"}).status_code == 422
    assert preview(client, photo["id"], {"length": 1000}).status_code == 422


def test_unknown_photo_is_404(client):
    response = preview(client, "does-not-exist", {})
    assert response.status_code == 404
    assert response.json() == {"detail": "Photo not found"}


def test_preview_sharpens_a_blurred_photo(client):
    # Catches parameters mixed up between the API and the engine (e.g. angle or length lost).
    psf = make_psf("motion", length=9, angle=30, radius=3)
    truth, observed = blurred_case(load_test_image(), psf, sigma=0.002)
    photo = upload(client, observed)
    response = preview(client, photo["id"], {"kernel": "motion", "length": 9, "angle": 30})
    restored = np.asarray(Image.open(BytesIO(response.content)), dtype=np.float64) / 255
    assert psnr(truth, restored) > psnr(truth, observed) + 1
