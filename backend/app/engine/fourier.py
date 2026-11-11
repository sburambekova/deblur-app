"""FFT helpers and the forward blur model.

The FFT treats the image as periodic, so blurring with a kernel k becomes a pointwise product:
F(k * x) = K . F(x), where K = psf_to_otf(k) is the transfer function (OTF) of the kernel.
Every deconvolution method in this engine inverts this model in one way or another.
"""

import numpy as np
from scipy import fft


# scipy's FFT on all CPU cores is about 9x faster than numpy's on a 1600 px photo.
def fft2(x: np.ndarray) -> np.ndarray:
    return fft.fft2(x, workers=-1)


def ifft2(x: np.ndarray) -> np.ndarray:
    """Inverse FFT, real part only: our images are real, the imaginary part is rounding noise."""
    return np.real(fft.ifft2(x, workers=-1))


def psf_to_otf(psf: np.ndarray, shape: tuple[int, ...]) -> np.ndarray:
    """Transfer function of `psf` for an image of `shape` (like MATLAB psf2otf)."""
    padded = np.zeros(shape)
    kh, kw = psf.shape
    padded[:kh, :kw] = psf
    # The FFT treats index (0, 0) as the kernel centre. Without this roll the blurred and the
    # deblurred images would be shifted by half a kernel.
    padded = np.roll(padded, (-(kh // 2), -(kw // 2)), axis=(0, 1))
    return fft2(padded)


def convolve(img: np.ndarray, psf: np.ndarray) -> np.ndarray:
    """Circular convolution of one channel with `psf`: the blur model that deblurring inverts."""
    return ifft2(fft2(img) * psf_to_otf(psf, img.shape))
