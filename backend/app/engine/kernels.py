"""Blur kernels (PSF): straight-line motion and an out-of-focus disk.

Both are built in pixel space, are non-negative, sum to 1 and have an odd size, so the middle
pixel is the kernel centre. Lengths and radii are in pixels, angles in degrees counter-clockwise
from horizontal as seen on screen.
"""

import numpy as np

SAMPLES_PER_PX = 20  # motion: points per pixel of segment length
SUPERSAMPLE = 8  # defocus: sub-pixels per pixel side


def motion_psf(length: float, angle: float) -> np.ndarray:
    """Motion blur along a segment of `length` px at `angle` degrees counter-clockwise."""
    if length <= 1:
        return np.ones((1, 1))
    half = int(np.ceil(length / 2))
    psf = np.zeros((2 * half + 1, 2 * half + 1))

    # Each sample of the segment is split between its 4 nearest pixels (bilinear weights).
    # Rounding samples to the nearest pixel gave the same jagged kernel for lengths 10.2 and 10.8.
    n = int(np.ceil(length)) * SAMPLES_PER_PX
    t = ((np.arange(n) + 0.5) / n - 0.5) * length
    a = np.deg2rad(angle)
    x = half + t * np.cos(a)
    # Rows grow downwards, so counter-clockwise on screen means y goes down.
    y = half - t * np.sin(a)
    col, row = np.floor(x).astype(int), np.floor(y).astype(int)
    dx, dy = x - col, y - row
    np.add.at(psf, (row, col), (1 - dx) * (1 - dy))
    np.add.at(psf, (row, col + 1), dx * (1 - dy))
    np.add.at(psf, (row + 1, col), (1 - dx) * dy)
    np.add.at(psf, (row + 1, col + 1), dx * dy)
    return psf / psf.sum()


def defocus_psf(radius: float) -> np.ndarray:
    """Uniform disk of `radius` px; edge pixels get the share of their area inside the disk."""
    if radius <= 0.5:
        return np.ones((1, 1))
    half = int(np.ceil(radius))
    n = 2 * half + 1
    s = SUPERSAMPLE
    # Sub-pixel centres, with 0 at the centre of the middle pixel.
    coords = (np.arange(n * s) + 0.5) / s - half - 0.5
    x, y = np.meshgrid(coords, coords)
    inside = (x**2 + y**2 <= radius**2).astype(float)
    psf = inside.reshape(n, s, n, s).sum(axis=(1, 3))
    return psf / psf.sum()


def make_psf(kernel: str, length: float, angle: float, radius: float) -> np.ndarray:
    """Kernel from API parameters: motion uses length and angle, defocus uses radius."""
    if kernel == "motion":
        return motion_psf(length, angle)
    if kernel == "defocus":
        return defocus_psf(radius)
    raise ValueError(f"unknown kernel {kernel!r}")
