from app.engine.kernels import make_psf
from tests.helpers import blurred_case, load_test_image
from tests.test_api_preview import upload


def estimate(client, photo_id: str, kernel: str):
    return client.post(f"/api/photos/{photo_id}/estimate", json={"kernel": kernel})


def test_motion_estimate(client):
    psf = make_psf("motion", length=20, angle=45, radius=3)
    _, observed = blurred_case(load_test_image(), psf, sigma=0.002)
    photo = upload(client, observed)
    response = estimate(client, photo["id"], "motion")
    assert response.status_code == 200
    body = response.json()
    assert body["kernel"] == "motion" and body["radius"] is None
    assert abs(body["length"] - 20) <= 2 and abs(body["angle"] - 45) <= 5


def test_defocus_estimate(client):
    psf = make_psf("defocus", length=1, angle=0, radius=6)
    _, observed = blurred_case(load_test_image(), psf, sigma=0.002)
    photo = upload(client, observed)
    body = estimate(client, photo["id"], "defocus").json()
    assert body["kernel"] == "defocus" and body["length"] is None
    assert abs(body["radius"] - 6) <= 0.5


def test_unknown_photo_is_404(client):
    assert estimate(client, "does-not-exist", "motion").status_code == 404


def test_bad_kernel_is_422(client):
    photo = upload(client, load_test_image())
    assert estimate(client, photo["id"], "blob").status_code == 422
