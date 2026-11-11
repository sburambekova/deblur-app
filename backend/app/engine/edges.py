"""Border handling before FFT deconvolution.

The FFT treats the image as periodic, but on a real photo the left edge does not match the
right one, and deconvolution turns that jump into ringing. edge_taper blends the borders into a
circularly blurred copy of the image (like MATLAB edgetaper). Near the borders the image then
looks exactly like the periodic blur the FFT model assumes, so there is nothing to ring.
"""

import numpy as np

from app.engine.fourier import convolve


def taper_window(n: int, width: int) -> np.ndarray:
    """1 in the middle, smooth half-cosine fall to 0 over `width` px at both ends."""
    d = np.minimum(np.arange(n), np.arange(n)[::-1])
    return np.where(d < width, 0.5 - 0.5 * np.cos(np.pi * d / width), 1.0)


def edge_taper(img: np.ndarray, psf: np.ndarray) -> np.ndarray:
    """Blend one channel into its circular blur near the borders, over the kernel size."""
    w = np.outer(taper_window(img.shape[0], psf.shape[0]), taper_window(img.shape[1], psf.shape[1]))
    return w * img + (1 - w) * convolve(img, psf)
