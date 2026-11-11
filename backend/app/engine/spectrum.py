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
    # A one-colour image has nothing to show; the prototype returned NaN here (0 / 0).
    # Checked on the input: the rounding error of the mean would otherwise leave tiny noise
    # that the scaling below stretches to [0, 1].
    if gray.max() == gray.min():
        return np.zeros_like(gray)
    h, w = gray.shape
    # Without the Hann window the image borders give a bright cross through the centre that
    # hides the dark stripes left by the blur.
    window = np.outer(np.hanning(h), np.hanning(w))
    spec = np.log1p(np.abs(np.fft.fftshift(fft2((gray - gray.mean()) * window))))
    lo, hi = spec.min(), spec.max()
    return (spec - lo) / (hi - lo)
