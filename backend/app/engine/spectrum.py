"""Log-magnitude spectrum of a photo, shown to the user next to the sliders.

Blur leaves a pattern in the spectrum: parallel dark stripes across the motion direction for
motion blur, rings for defocus. log_spectrum = log(1 + |FFT|) of the windowed image with the
zero frequency in the centre, scaled to [0, 1] for display.
"""

import numpy as np

from app.engine.fourier import fft2

LUMA = np.array([0.299, 0.587, 0.114])  # ITU-R BT.601 weights


def to_gray(rgb: np.ndarray) -> np.ndarray:
    return rgb @ LUMA


def log_spectrum(gray: np.ndarray) -> np.ndarray:
    """2D spectrum in [0, 1], zero frequency in the centre."""
    h, w = gray.shape
    # Without the Hann window the image borders give a bright cross through the centre that
    # hides the dark stripes left by the blur.
    window = np.outer(np.hanning(h), np.hanning(w))
    spec = np.log1p(np.abs(np.fft.fftshift(fft2((gray - gray.mean()) * window))))
    lo, hi = spec.min(), spec.max()
    # A flat image has a flat spectrum. The prototype divided 0 by 0 here and returned NaN.
    if hi == lo:
        return np.zeros_like(spec)
    return (spec - lo) / (hi - lo)
