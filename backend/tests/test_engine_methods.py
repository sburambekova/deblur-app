"""Deconvolution methods on circular_case: the frame is periodic, so borders do not interfere.

Thresholds come from real runs with a margin. Measured values are in the comments.
"""

import numpy as np
import pytest

from app.engine.kernels import defocus_psf, motion_psf
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
