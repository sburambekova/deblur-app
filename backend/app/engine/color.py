"""Conversion between sRGB values and linear light.

Image files store brightness gamma-encoded (sRGB), but blur adds up light linearly. So the blur
model k * x only holds after srgb_to_linear, and the result goes back through linear_to_srgb.
Both use the exact piecewise sRGB formula, not the x ** 2.2 approximation.
"""

import numpy as np


def srgb_to_linear(x: np.ndarray) -> np.ndarray:
    """Linear segment below 0.04045, power 2.4 above."""
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x: np.ndarray) -> np.ndarray:
    """Inverse of srgb_to_linear."""
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)
