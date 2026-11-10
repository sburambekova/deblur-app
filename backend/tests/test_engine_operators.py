import numpy as np

from app.engine.operators import grad, grad_spectrum, grad_t


def test_grad_t_is_adjoint_of_grad():
    rng = np.random.default_rng(0)
    x, vx, vy = rng.normal(size=(3, 40, 30))
    gx, gy = grad(x)
    assert np.isclose((gx * vx + gy * vy).sum(), (x * grad_t(vx, vy)).sum())


def test_grad_spectrum_is_fft_of_grad_t_grad():
    # TV and Tikhonov H1 rely on grad_t(grad(.)) being this pointwise product in Fourier space.
    delta = np.zeros((32, 24))
    delta[0, 0] = 1
    response = np.fft.fft2(grad_t(*grad(delta)))
    assert np.allclose(response, grad_spectrum(delta.shape), rtol=0, atol=1e-12)


def test_grad_spectrum_range_does_not_depend_on_size():
    for shape in [(8, 8), (512, 384), (1200, 1600)]:
        spec = grad_spectrum(shape)
        assert spec.min() == 0 and spec.max() <= 8
