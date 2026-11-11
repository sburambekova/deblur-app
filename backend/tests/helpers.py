"""Test helpers: PSNR and synthetic blurred images with a known kernel."""

from collections.abc import Callable
from pathlib import Path

import numpy as np
from PIL import Image

from app.engine.color import linear_to_srgb, srgb_to_linear
from app.engine.fourier import convolve

DATA_DIR = Path(__file__).parent / "data"


def psnr(truth: np.ndarray, test: np.ndarray) -> float:
    """Peak signal-to-noise ratio in dB for images in [0, 1]."""
    mse = np.mean((truth - test) ** 2)
    return 10 * np.log10(1 / mse)


def load_test_image() -> np.ndarray:
    """tests/data/source_image.png as RGB float64 in [0, 1]."""
    img = Image.open(DATA_DIR / "source_image.png").convert("RGB")
    return np.asarray(img, dtype=np.float64) / 255.0


def _blur_srgb(sharp: np.ndarray, psf: np.ndarray) -> np.ndarray:
    # Blur adds up light linearly, so it is applied in linear light, not to sRGB values.
    lin = srgb_to_linear(sharp)
    blurred = np.stack([convolve(lin[..., c], psf) for c in range(3)], axis=-1)
    return linear_to_srgb(blurred)


def _add_noise(img: np.ndarray, sigma: float, seed: int) -> np.ndarray:
    noisy = img + np.random.default_rng(seed).normal(0, sigma, img.shape)
    return np.clip(noisy, 0, 1)


def blurred_case(
    sharp: np.ndarray, psf: np.ndarray, sigma: float, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Blur, crop the border by the kernel size, add noise. Returns (truth, observed)."""
    # FFT blur is circular; cropping makes the frame non-periodic, like a real photo
    # where the blur pulls in light from outside the frame.
    k = max(psf.shape)
    truth = sharp[k:-k, k:-k]
    observed = _blur_srgb(sharp, psf)[k:-k, k:-k]
    return truth, _add_noise(observed, sigma, seed)


def circular_case(
    sharp: np.ndarray, psf: np.ndarray, sigma: float, seed: int = 0
) -> tuple[np.ndarray, np.ndarray]:
    """Like blurred_case but without cropping: the frame stays periodic, borders do not matter."""
    return sharp, _add_noise(_blur_srgb(sharp, psf), sigma, seed)


def restore(
    observed: np.ndarray, method: Callable[..., np.ndarray], psf: np.ndarray, **params
) -> np.ndarray:
    """Apply a one-channel method to an sRGB image in linear light, without border handling."""
    lin = srgb_to_linear(observed)
    out = np.stack([method(lin[..., c], psf, **params) for c in range(3)], axis=-1)
    return linear_to_srgb(np.clip(out, 0, 1))
