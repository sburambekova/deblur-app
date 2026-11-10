"""New engine vs the prototype in tests/reference. Comparisons are added step by step in phase 2."""

import numpy as np

from app.engine import color, fourier, kernels, operators
from app.engine.methods.tikhonov import tikhonov
from tests.helpers import blurred_case, load_test_image
from tests.reference import real_deblur_prototype as rd


def same(new: np.ndarray, old: np.ndarray) -> bool:
    # rtol=0: the default relative tolerance of allclose (1e-5) would make the check much weaker.
    return np.allclose(new, old, rtol=0, atol=1e-9)


def test_prototype_imports_and_blurred_case_is_cropped():
    sharp = load_test_image()
    psf = rd.motion_psf(15, 30)
    truth, observed = blurred_case(sharp, psf, sigma=0.01)
    k = psf.shape[0]
    h, w = sharp.shape[:2]
    assert truth.shape == observed.shape == (h - 2 * k, w - 2 * k, 3)


def test_color():
    x = np.linspace(0, 1, 1001)
    assert same(color.srgb_to_linear(x), rd.srgb_to_linear(x))
    assert same(color.linear_to_srgb(x), rd.linear_to_srgb(x))


def test_psf_to_otf_and_convolve():
    rng = np.random.default_rng(0)
    img = rng.random((64, 48))
    for size in [(1, 1), (5, 5), (5, 9), (15, 15)]:
        psf = rng.random(size)
        assert same(fourier.psf_to_otf(psf, img.shape), rd.psf_to_otf(psf, img.shape))
        assert same(fourier.convolve(img, psf), rd.blur(img, psf))


def test_gradient():
    rng = np.random.default_rng(0)
    x, vx, vy = rng.normal(size=(3, 40, 30))
    for new, old in zip(operators.grad(x), rd.grad(x)):
        assert same(new, old)
    assert same(operators.grad_t(vx, vy), rd.grad_t(vx, vy))
    assert same(operators.grad_spectrum(x.shape), rd.penalty_spectrum(x.shape, "H1"))


def test_motion_kernel():
    for length in [0.5, 1, 1.5, 6, 10.2, 15, 33.3, 60]:
        for angle in [0, 15, 30, 45, 90, 137, 180]:
            new = kernels.motion_psf(length, angle)
            old = rd.motion_psf(length, angle)
            assert new.shape == old.shape and same(new, old)


def test_defocus_kernel():
    for radius in [0.5, 1, 2.5, 3, 5, 12.3, 25]:
        new = kernels.defocus_psf(radius)
        old = rd.defocus_psf(radius)
        assert new.shape == old.shape and same(new, old)


def test_make_psf():
    for p in [
        {"kernel": "motion", "length": 15, "angle": 30, "radius": 3},
        {"kernel": "defocus", "length": 15, "angle": 30, "radius": 5},
    ]:
        assert same(kernels.make_psf(**p), rd.make_psf(p))


def test_tikhonov():
    img = np.random.default_rng(0).random((64, 48))
    for psf in [rd.motion_psf(15, 30), rd.defocus_psf(5)]:
        for mu in [1e-6, 0.01, 0.1]:
            for penalty in ["L2", "H1"]:
                new = tikhonov(img, psf, mu, penalty)
                assert same(new, rd.deconvolve(img, psf, mu, penalty))
