"""Guess the blur kernel from the photo itself, for the Auto button.

Blurring multiplies the spectrum by the kernel's transfer function K, so the log spectrum is
log|X| + log|K|: a sum. The cepstrum, the inverse FFT of the log spectrum, keeps this sum and
separates the two parts. The photo's part sits near the centre. The kernel's zeros, the dark
stripes or rings in the spectrum, repeat at a regular step and give a strong negative value:
- motion along a segment of `length` px: |K| has zeros every 1/length across the motion, so
  there are two dark points at distance `length` from the centre along the motion direction;
- a defocus disk of `radius` px: the zeros of |K| repeat about every 1/(2 radius), so there is
  a dark ring at about 2 * radius.

This is a starting point, not a guarantee: a curved hand shake has no straight line to find,
and strong texture in the photo can win over the kernel. The user checks it on the spectrum.
"""

import numpy as np

from app.engine.fourier import fft2, ifft2

# Closer than this the centre of the cepstrum is dark by itself. 60 px is the longest blur the
# sliders allow, so a dark point further away cannot be the answer.
MIN_DIST = 4
MAX_DIST = 60


def cepstrum(gray: np.ndarray) -> np.ndarray:
    """Real cepstrum with the zero in the centre."""
    h, w = gray.shape
    # The Hann window keeps the image borders from adding their own stripes to the spectrum.
    window = np.outer(np.hanning(h), np.hanning(w))
    # 1e-3 keeps log away from -inf where the spectrum is exactly zero.
    log_spec = np.log(np.abs(fft2((gray - gray.mean()) * window)) + 1e-3)
    return np.fft.fftshift(ifft2(log_spec))


def _distances(shape: tuple[int, ...]) -> tuple[np.ndarray, int, int]:
    """Distance of each pixel from the centre that fftshift uses, and that centre."""
    cy, cx = shape[0] // 2, shape[1] // 2
    yy, xx = np.indices(shape)
    return np.hypot(yy - cy, xx - cx), cy, cx


def estimate_motion(gray: np.ndarray) -> tuple[float, float]:
    """(length in px, angle in degrees counter-clockwise from horizontal, 0 to 180)."""
    cep = cepstrum(gray)
    dist, cy, cx = _distances(cep.shape)
    cep[(dist < MIN_DIST) | (dist > MAX_DIST)] = np.inf
    y, x = np.unravel_index(np.argmin(cep), cep.shape)
    # Row indices grow downwards, angles go up on screen (as in kernels.motion_psf).
    dx, dy = x - cx, cy - y
    # The cepstrum is symmetric, so the point and its mirror give the same line: angle mod 180.
    return float(np.hypot(dx, dy)), float(np.degrees(np.arctan2(dy, dx)) % 180)


def estimate_defocus(gray: np.ndarray) -> float:
    """Radius in px: half the radius of the darkest ring of the cepstrum."""
    cep = cepstrum(gray)
    dist, _, _ = _distances(cep.shape)
    ring = np.round(dist).astype(int).ravel()
    # Mean of the cepstrum over each ring of whole-pixel radius.
    radial = np.bincount(ring, cep.ravel()) / np.bincount(ring)
    r = MIN_DIST + int(np.argmin(radial[MIN_DIST : MAX_DIST + 1]))
    return r / 2
