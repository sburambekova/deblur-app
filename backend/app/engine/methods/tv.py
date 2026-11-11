"""Total variation (TV) deconvolution of one channel, solved with ADMM.

Minimises 0.5 |k * x - g|^2 + lam * sum |grad x|. The L1 norm of the gradient smooths flat
areas but keeps edges sharp; with large lam the image looks posterised.
ADMM introduces z = grad x (u is the scaled multiplier) and alternates two easy steps:
  x step: X = (conj(K) G + rho F(grad_t(z - u))) / (|K|^2 + rho |D|^2), one Fourier division;
  z step: shorten every vector grad x + u by lam / rho, keeping its direction.
"""

import numpy as np

from app.engine.fourier import fft2, ifft2, psf_to_otf
from app.engine.operators import grad, grad_spectrum, grad_t


def tv(img: np.ndarray, psf: np.ndarray, lam: float, iters: int = 50) -> np.ndarray:
    """Deblur one channel in linear light. Larger lam gives flatter areas and less noise."""
    # rho only changes how fast ADMM converges, not the minimum it reaches. rho = 10 lam is a
    # scale heuristic; with it 30 and 200 iterations give the same image, so 50 is enough.
    rho = 10 * lam
    otf = psf_to_otf(psf, img.shape)
    data = np.conj(otf) * fft2(img)
    denom = np.abs(otf) ** 2 + rho * grad_spectrum(img.shape)
    zx = zy = ux = uy = np.zeros_like(img)
    for _ in range(iters):
        # Gradients go through np.roll, not FFTs: 2 FFTs per iteration instead of 6.
        x = ifft2((data + rho * fft2(grad_t(zx - ux, zy - uy))) / denom)
        gx, gy = grad(x)
        vx, vy = gx + ux, gy + uy
        # 1e-12 keeps zero-length vectors from dividing by zero.
        shrink = np.maximum(1 - lam / (rho * np.maximum(np.hypot(vx, vy), 1e-12)), 0)
        zx, zy = shrink * vx, shrink * vy
        ux, uy = vx - zx, vy - zy
    return x
