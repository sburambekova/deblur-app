import numpy as np
import pytest

from app.engine.estimate import estimate_defocus, estimate_motion
from app.engine.kernels import make_psf
from app.engine.spectrum import to_gray
from tests.helpers import blurred_case, load_test_image


def blurred_gray(kernel: str, length: float = 1, angle: float = 0, radius: float = 1):
    psf = make_psf(kernel, length, angle, radius)
    _, observed = blurred_case(load_test_image(), psf, sigma=0.002)
    return to_gray(observed)


def angle_error(a: float, b: float) -> float:
    """0 and 180 degrees are the same line."""
    d = abs(a - b) % 180
    return min(d, 180 - d)


@pytest.mark.parametrize("length", [10, 20, 30])
@pytest.mark.parametrize("angle", [0, 45, 120])
def test_motion_is_found(length, angle):
    est_length, est_angle = estimate_motion(blurred_gray("motion", length=length, angle=angle))
    assert abs(est_length - length) <= 2
    assert angle_error(est_angle, angle) <= 5


@pytest.mark.parametrize("radius", [3, 6, 10])
def test_defocus_is_found(radius):
    assert abs(estimate_defocus(blurred_gray("defocus", radius=radius)) - radius) <= 0.5


def test_angle_is_between_0_and_180():
    _, angle = estimate_motion(np.random.default_rng(0).random((128, 128)))
    assert 0 <= angle < 180
