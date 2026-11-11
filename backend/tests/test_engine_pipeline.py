"""Border handling, spectrum and the full pipeline on blurred_case (a non-periodic frame).

Thresholds come from real runs with a margin. Measured values are in the comments.
"""

import numpy as np
import pytest

from app.engine.edges import edge_taper, taper_window
from app.engine.kernels import defocus_psf, motion_psf
from app.engine.pipeline import deblur, scale_params
from app.engine.spectrum import log_spectrum, to_gray
from tests.helpers import blurred_case, load_test_image, psnr

CASES = {"motion": motion_psf(15, 30), "defocus": defocus_psf(5)}


@pytest.fixture(scope="module")
def sharp() -> np.ndarray:
    return load_test_image()


def test_taper_window():
    w = taper_window(100, 10)
    assert w[0] == 0 and w[-1] == 0
    assert np.all(w[10:90] == 1)
    assert np.all(np.diff(w[:11]) > 0)


def test_edge_taper_keeps_the_middle():
    img = np.random.default_rng(0).random((64, 64))
    psf = motion_psf(9, 0)
    k = psf.shape[0]
    tapered = edge_taper(img, psf)
    assert np.array_equal(tapered[k:-k, k:-k], img[k:-k, k:-k])
    assert not np.allclose(tapered[0], img[0])


def test_deblur_improves_every_method(sharp):
    # sigma 0.01, default parameters. Motion 18.8 dB blurred -> Tikhonov 20.2, TV 22.0,
    # R-L 22.0. Defocus 19.5 -> 20.8, 22.5, 22.4.
    for psf in CASES.values():
        truth, observed = blurred_case(sharp, psf, sigma=0.01)
        for method in ["tikhonov", "tv", "rl"]:
            restored = deblur(observed, psf, method)
            assert restored.shape == observed.shape
            assert psnr(truth, restored) > psnr(truth, observed) + 1


def test_wrong_kernel_makes_it_worse(sharp):
    # Same length, perpendicular direction: 18.8 -> 15.8 dB. This is what shows that the
    # pipeline actually uses the kernel and does not just sharpen everything.
    truth, observed = blurred_case(sharp, motion_psf(15, 30), sigma=0.01)
    restored = deblur(observed, motion_psf(15, 120), "tikhonov")
    assert psnr(truth, restored) < psnr(truth, observed)


def test_tv_and_rl_beat_tikhonov(sharp):
    # Tikhonov H1 mu 0.01 is the best Tikhonov here: motion 20.4, defocus 21.0 dB.
    # TV: 22.0 and 22.5. R-L: 22.0 and 22.4.
    for psf in CASES.values():
        truth, observed = blurred_case(sharp, psf, sigma=0.01)
        tik = psnr(truth, deblur(observed, psf, "tikhonov", mu=0.01, penalty="H1"))
        assert psnr(truth, deblur(observed, psf, "tv")) > tik + 1
        assert psnr(truth, deblur(observed, psf, "rl")) > tik + 1


def test_unknown_method():
    with pytest.raises(ValueError):
        deblur(np.zeros((16, 16, 3)), np.ones((1, 1)), "wiener")


def test_scale_params():
    p = {"kernel": "motion", "length": 10, "angle": 30, "radius": 2, "method": "rl",
         "mu": 0.01, "penalty": "H1", "lam": 1e-3, "iters": 80}  # fmt: skip
    q = scale_params(p, 3)
    assert (q["length"], q["radius"]) == (30, 6)
    assert np.isclose(q["mu"], 0.09) and np.isclose(q["lam"], 3e-3)
    assert (q["angle"], q["iters"], q["kernel"], q["method"]) == (30, 80, "motion", "rl")
    assert scale_params(dict(p, penalty="L2"), 3)["mu"] == 0.01
    assert p["length"] == 10  # the input is not changed


def test_spectrum_range(sharp):
    spec = log_spectrum(to_gray(sharp))
    assert spec.shape == sharp.shape[:2]
    assert spec.min() == 0 and spec.max() == 1


def test_spectrum_of_flat_image_has_no_nan():
    # Deliberate difference from the prototype, which returned NaN here (0 / 0).
    assert np.array_equal(log_spectrum(np.zeros((32, 48))), np.zeros((32, 48)))
    spec = log_spectrum(np.full((32, 48), 0.3))
    assert not np.isnan(spec).any() and spec.min() >= 0 and spec.max() <= 1


def test_to_gray():
    assert np.isclose(to_gray(np.ones((4, 4, 3))), 1).all()
