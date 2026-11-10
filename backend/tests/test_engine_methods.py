"""Deconvolution methods on circular_case: the frame is periodic, so borders do not interfere.

Thresholds come from real runs with a margin. Measured values are in the comments.
"""

import numpy as np
import pytest

from app.engine.color import srgb_to_linear
from app.engine.fourier import convolve
from app.engine.kernels import defocus_psf, motion_psf
from app.engine.methods.richardson_lucy import richardson_lucy
from app.engine.methods.tikhonov import tikhonov
from tests.helpers import circular_case, load_test_image, psnr, restore

CASES = {"motion": motion_psf(15, 30), "defocus": defocus_psf(5)}


@pytest.fixture(scope="module")
def sharp() -> np.ndarray:
    return load_test_image()


def test_tikhonov_improves_noisy_image(sharp):
    # sigma 0.01, mu 0.01: motion 18.3 -> 20.4 (L2) / 21.0 (H1) dB, defocus 19.0 -> 20.8 / 21.0.
    for psf in CASES.values():
        truth, observed = circular_case(sharp, psf, sigma=0.01)
        for penalty in ["L2", "H1"]:
            restored = restore(observed, tikhonov, psf, mu=0.01, penalty=penalty)
            assert psnr(truth, restored) > psnr(truth, observed) + 1


def test_tikhonov_without_noise_almost_restores(sharp):
    # mu 1e-8: motion 42.8 dB, defocus 44.0 dB. The blurred input is about 18-19 dB.
    for psf in CASES.values():
        truth, observed = circular_case(sharp, psf, sigma=0)
        restored = restore(observed, tikhonov, psf, mu=1e-8)
        assert psnr(truth, restored) > 40


def test_tikhonov_unknown_penalty():
    with pytest.raises(ValueError):
        tikhonov(np.zeros((8, 8)), np.ones((1, 1)), 0.01, "L1")


def test_rl_stays_non_negative_on_black():
    # FFT rounding gives values like -1e-17 where the image is black, never more.
    img = np.zeros((64, 64))
    img[20:40, 25:35] = 1
    psf = CASES["motion"]
    out = richardson_lucy(convolve(img, psf), psf, 30)
    assert out.min() >= -1e-12


def test_rl_keeps_total_brightness(sharp):
    _, observed = circular_case(sharp, CASES["defocus"], sigma=0.01)
    channel = srgb_to_linear(observed[..., 0])
    out = richardson_lucy(channel, CASES["defocus"], 30)
    assert np.isclose(out.sum(), channel.sum(), rtol=1e-9)


def test_rl_beats_tikhonov(sharp):
    # sigma 0.01: motion Tikhonov 21.0, R-L 22.8 dB; defocus Tikhonov 21.0, R-L 22.6 dB.
    # Tikhonov H1 with mu 0.01 is within 0.1 dB of its best mu on both cases.
    for psf in CASES.values():
        truth, observed = circular_case(sharp, psf, sigma=0.01)
        tik = restore(observed, tikhonov, psf, mu=0.01, penalty="H1")
        rl = restore(observed, richardson_lucy, psf, iters=80)
        assert psnr(truth, rl) > psnr(truth, tik) + 1
