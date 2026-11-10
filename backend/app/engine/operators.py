"""Discrete image gradient with periodic borders, its adjoint, and their spectrum.

grad uses forward differences, grad_t is its adjoint: <grad x, v> = <x, grad_t v>.
grad_t(grad(x)) is a convolution, so in Fourier space it is a pointwise product with
grad_spectrum = (2 sin(pi fx))^2 + (2 sin(pi fy))^2, with fx, fy in cycles per pixel.
This is the H1 penalty of Tikhonov and part of the x step of TV.
"""

import numpy as np


def grad(x: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Forward differences along x (columns) and y (rows), wrapping around at the borders."""
    return np.roll(x, -1, axis=1) - x, np.roll(x, -1, axis=0) - x


def grad_t(gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
    """Adjoint (transpose) of grad."""
    return (np.roll(gx, 1, axis=1) - gx) + (np.roll(gy, 1, axis=0) - gy)


def grad_spectrum(shape: tuple[int, ...]) -> np.ndarray:
    """Fourier spectrum of grad_t(grad(.)) on an image of `shape`."""
    # Normalised frequencies keep the values in [0, 8] for any image size, so mu and lam mean
    # the same thing on every photo.
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.fftfreq(shape[1])[None, :]
    return (2 * np.sin(np.pi * fx)) ** 2 + (2 * np.sin(np.pi * fy)) ** 2
