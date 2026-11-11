import numpy as np

from app.engine.fourier import convolve, fft2, ifft2, psf_to_otf


def test_ifft2_inverts_fft2():
    img = np.random.default_rng(0).random((40, 30))
    assert np.allclose(ifft2(fft2(img)), img, rtol=0, atol=1e-12)


def test_otf_of_delta_is_one():
    otf = psf_to_otf(np.ones((1, 1)), (64, 48))
    assert np.allclose(otf, 1, rtol=0, atol=1e-12)


def test_convolve_with_delta_keeps_image():
    img = np.random.default_rng(0).random((40, 30))
    assert np.allclose(convolve(img, np.ones((1, 1))), img, rtol=0, atol=1e-12)


def test_kernel_is_centred_on_the_pixel():
    # One bright pixel blurs into a copy of the kernel centred on that pixel, not shifted.
    psf = np.random.default_rng(1).random((5, 7))
    img = np.zeros((32, 32))
    img[10, 20] = 1
    out = convolve(img, psf)
    assert np.allclose(out[8:13, 17:24], psf, rtol=0, atol=1e-12)


def test_convolve_keeps_total_brightness():
    rng = np.random.default_rng(2)
    img = rng.random((40, 30))
    psf = rng.random((5, 5))
    psf /= psf.sum()
    assert np.isclose(convolve(img, psf).sum(), img.sum())
