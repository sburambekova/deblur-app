"""Tikhonov deconvolution of one channel.

Minimises |k * x - g|^2 + mu |p * x|^2. Both terms are diagonal in Fourier space, so the
minimiser is one division: X = conj(K) G / (|K|^2 + mu |P|^2).
L2 penalty: |P|^2 = 1 (keeps x small). H1 penalty: |P|^2 = grad_spectrum (keeps its gradient
small). Fast enough for the live preview, but as a linear filter it lifts noise together with
detail, which shows up as grain and stripes along the motion.
"""

import numpy as np

from app.engine.fourier import fft2, ifft2, psf_to_otf
from app.engine.operators import grad_spectrum


def tikhonov(img: np.ndarray, psf: np.ndarray, mu: float, penalty: str = "L2") -> np.ndarray:
    """Deblur one channel in linear light. Larger mu gives less noise and less detail."""
    if penalty == "L2":
        reg = 1.0
    elif penalty == "H1":
        reg = grad_spectrum(img.shape)
    else:
        raise ValueError(f"unknown penalty {penalty!r}, expected 'L2' or 'H1'")
    otf = psf_to_otf(psf, img.shape)
    return ifft2(np.conj(otf) * fft2(img) / (np.abs(otf) ** 2 + mu * reg))
