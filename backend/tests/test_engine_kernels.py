import numpy as np
import pytest

from app.engine.kernels import defocus_psf, make_psf, motion_psf

MOTION = [(1.5, 0), (7.5, 30), (15, 0), (15, 90), (40, 137), (60, 180)]
RADII = [1, 2.5, 5, 12.3, 25]


def check_basic(psf: np.ndarray) -> None:
    assert np.isclose(psf.sum(), 1)
    assert psf.min() >= 0
    assert psf.shape[0] == psf.shape[1] and psf.shape[0] % 2 == 1


def test_motion_basic_properties():
    for length, angle in MOTION:
        check_basic(motion_psf(length, angle))


def test_defocus_basic_properties():
    for radius in RADII:
        check_basic(defocus_psf(radius))


def test_motion_centre_of_mass_is_the_centre_pixel():
    # Otherwise deblurring would shift the image.
    for angle in range(0, 181, 15):
        psf = motion_psf(12.7, angle)
        rows, cols = np.indices(psf.shape)
        centre = psf.shape[0] // 2
        assert np.isclose((psf * rows).sum(), centre)
        assert np.isclose((psf * cols).sum(), centre)


def test_motion_direction():
    assert motion_psf(15, 0).sum(axis=1).max() > 0.999  # one row
    assert motion_psf(15, 90).sum(axis=0).max() > 0.999  # one column
    # 45 degrees counter-clockwise on screen goes up and to the right.
    psf = motion_psf(15, 45)
    c = psf.shape[0] // 2
    assert psf[:c, c + 1 :].sum() > 0.4  # upper right
    assert psf[:c, :c].sum() == 0  # upper left


def test_fractional_length_changes_kernel():
    assert not np.allclose(motion_psf(10.2, 30), motion_psf(10.8, 30))


def test_defocus_is_symmetric():
    for radius in RADII:
        psf = defocus_psf(radius)
        assert np.allclose(psf, psf.T)
        assert np.allclose(psf, psf[::-1, :])


def test_tiny_kernels_are_delta():
    assert np.array_equal(motion_psf(1, 45), [[1.0]])
    assert np.array_equal(defocus_psf(0.5), [[1.0]])


def test_make_psf_picks_the_kernel():
    assert np.array_equal(make_psf("motion", 15, 30, 3), motion_psf(15, 30))
    assert np.array_equal(make_psf("defocus", 15, 30, 3), defocus_psf(3))
    with pytest.raises(ValueError):
        make_psf("gauss", 15, 30, 3)
