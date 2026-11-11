"""Deblurring of a whole sRGB photo: the entry point for the services.

deblur: sRGB -> linear light -> for each channel edge_taper, then the chosen method ->
clip to [0, 1] -> sRGB. The same kernel is used for all three channels.
scale_params converts parameters chosen on the preview to another size of the same photo.
"""

import numpy as np

from app.engine.color import linear_to_srgb, srgb_to_linear
from app.engine.edges import edge_taper
from app.engine.methods.richardson_lucy import richardson_lucy
from app.engine.methods.tikhonov import tikhonov
from app.engine.methods.tv import tv


def deblur(
    rgb: np.ndarray,
    psf: np.ndarray,
    method: str,
    *,
    mu: float = 0.01,
    penalty: str = "L2",
    lam: float = 5e-4,
    iters: int = 80,
) -> np.ndarray:
    """Deblur an sRGB image (H x W x 3, floats in [0, 1]); returns the same shape and range.

    tikhonov uses mu and penalty, tv uses lam, rl (Richardson-Lucy) uses iters.
    """
    lin = srgb_to_linear(rgb)
    channels = []
    for c in range(3):
        img = edge_taper(lin[..., c], psf)
        if method == "tikhonov":
            out = tikhonov(img, psf, mu, penalty)
        elif method == "tv":
            # TV keeps its own fixed number of iterations; `iters` is for R-L only.
            out = tv(img, psf, lam)
        elif method == "rl":
            out = richardson_lucy(img, psf, iters)
        else:
            raise ValueError(f"unknown method {method!r}")
        channels.append(out)
    # Amplified noise goes below 0 and above 1 in linear light; sRGB is only defined in [0, 1].
    return linear_to_srgb(np.clip(np.stack(channels, axis=-1), 0, 1))


def scale_params(params: dict, s: float) -> dict:
    """Parameters for the same photo resized by factor s (preview -> full size: s > 1)."""
    p = dict(params, length=params["length"] * s, radius=params["radius"] * s)
    # L2: the filter depends only on |K|^2 + mu, which does not change with size.
    # H1: |P|^2 ~ f^2 and a detail at frequency f moves to f / s, so mu * s^2 keeps the filter.
    if p["penalty"] == "H1":
        p["mu"] = p["mu"] * s**2
    # TV: the data term sums over s^2 times more pixels while gradients get s times smaller,
    # so the TV term only grows by s. R-L iterations stay the same.
    p["lam"] = p["lam"] * s
    return p
