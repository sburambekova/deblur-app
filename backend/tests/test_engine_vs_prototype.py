"""New engine vs the prototype in tests/reference. Comparisons are added step by step in phase 2."""

from tests.helpers import blurred_case, load_test_image
from tests.reference import real_deblur_prototype as rd


def test_prototype_imports_and_blurred_case_is_cropped():
    sharp = load_test_image()
    psf = rd.motion_psf(15, 30)
    truth, observed = blurred_case(sharp, psf, sigma=0.01)
    k = psf.shape[0]
    h, w = sharp.shape[:2]
    assert truth.shape == observed.shape == (h - 2 * k, w - 2 * k, 3)
