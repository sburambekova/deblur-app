"""Richardson-Lucy deconvolution of one channel.

Update: x <- x . (k~ * (g / (k * x))), where k~ is the mirrored kernel (conj(K) in Fourier
space, a correlation). It is the EM algorithm for the most likely image under Poisson
(photon counting) noise. Every step multiplies by non-negative factors, so x stays
non-negative, and the total brightness stays equal to that of g.
There is no mu: the number of iterations is the regulariser. More iterations recover more
detail and amplify more noise.
"""

import numpy as np

from app.engine.fourier import fft2, ifft2, psf_to_otf


def richardson_lucy(img: np.ndarray, psf: np.ndarray, iters: int) -> np.ndarray:
    """Deblur one channel in linear light with `iters` multiplicative updates."""
    otf = psf_to_otf(psf, img.shape)
    # Noise can push values below 0; the method assumes light, which is never negative.
    img = np.maximum(img, 0)
    x = np.full_like(img, img.mean())
    for _ in range(iters):
        # The floor keeps black areas, where k * x is about 0, from dividing by zero.
        ratio = img / np.maximum(ifft2(fft2(x) * otf), 1e-6)
        x = x * ifft2(fft2(ratio) * np.conj(otf))
    return x
