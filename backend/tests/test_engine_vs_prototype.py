"""New engine vs the prototype in tests/reference. Comparisons are added step by step in phase 2."""

import numpy as np

from app.engine import color, edges, fourier, kernels, operators, pipeline, spectrum
from app.engine.methods.richardson_lucy import richardson_lucy
from app.engine.methods.tikhonov import tikhonov
from app.engine.methods.tv import tv
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


def test_richardson_lucy():
    # Some values below 0, so the clipping of the input is compared too.
    img = np.random.default_rng(0).normal(0.5, 0.3, (64, 48))
    for psf in [rd.motion_psf(15, 30), rd.defocus_psf(5)]:
        for iters in [1, 10, 30]:
            new = richardson_lucy(img, psf, iters)
            assert same(new, rd.richardson_lucy(img, psf, iters))


def test_tv():
    img = np.random.default_rng(0).random((64, 48))
    for psf in [rd.motion_psf(15, 30), rd.defocus_psf(5)]:
        for lam in [1e-5, 5e-4, 0.1]:
            for iters in [1, 50]:
                new = tv(img, psf, lam, iters)
                assert same(new, rd.tv_deconvolve(img, psf, lam, iters))


def test_edge_taper():
    img = np.random.default_rng(0).random((64, 48))
    for n, width in [(64, 1), (64, 15), (48, 31)]:
        assert same(edges.taper_window(n, width), rd.taper_window(n, width))
    for psf in [rd.motion_psf(15, 30), rd.defocus_psf(5)]:
        assert same(edges.edge_taper(img, psf), rd.edge_taper(img, psf))


def test_pipeline():
    sharp = load_test_image()
    for psf in [rd.motion_psf(15, 30), rd.defocus_psf(5)]:
        _, observed = blurred_case(sharp, psf, sigma=0.01)
        for method, params in [
            ("tikhonov", {"mu": 0.02, "penalty": "L2"}),
            ("tikhonov", {"mu": 0.01, "penalty": "H1"}),
            ("tv", {"lam": 5e-4}),
            ("rl", {"iters": 30}),
        ]:
            new = pipeline.deblur(observed, psf, method, **params)
            # The prototype requires mu even for methods that ignore it.
            old_params = {"mu": 0.01, **params}
            old = rd.deblur_photo(observed, psf, edge="taper", method=method, **old_params)
            assert same(new, old)


def test_scale_params():
    p = {"kernel": "motion", "length": 12.5, "angle": 30, "radius": 3.3, "method": "tv",
         "mu": 0.013, "penalty": "L2", "lam": 7e-4, "iters": 80}  # fmt: skip
    for penalty in ["L2", "H1"]:
        for s in [0.5, 1, 3.125]:
            q = dict(p, penalty=penalty)
            assert pipeline.scale_params(q, s) == rd.scale_params(q, s)


def test_spectrum():
    sharp = load_test_image()
    _, observed = blurred_case(sharp, rd.motion_psf(15, 30), sigma=0.01)
    gray = spectrum.to_gray(observed)
    assert same(gray, observed @ [0.299, 0.587, 0.114])
    assert same(spectrum.log_spectrum(gray), rd.log_spectrum(gray))
