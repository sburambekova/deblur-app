# Reference copy from LulaKebaber/Math_for_Imaging (branch mvp-real-photos, commit 2cb965b): test oracle only, not site code.
"""Tikhonov deblurring of real phone photos: colour, any aspect ratio, motion at any angle, defocus."""

import textwrap
from pathlib import Path

import numpy as np
from matplotlib.figure import Figure
from PIL import Image, ImageOps
from scipy import fft

ROOT = Path(__file__).parent
RAW_DIR = ROOT / "data" / "real_raw"
PHOTOS_DIR = ROOT / "data" / "real"
RESULTS_DIR = ROOT / "results" / "mvp"

FULL_SIDE = 1600


# scipy's FFT with all CPU cores is several times faster than numpy's on full-size
# photos, which matters for the iterative methods below.
def fft2(x):
    return fft.fft2(x, workers=-1)


def ifft2(x):
    return np.real(fft.ifft2(x, workers=-1))


def load_photo(path, max_side: int = 512) -> np.ndarray:
    """Load an RGB photo as float64 in [0, 1], upright, larger side at most max_side."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"no such file: {path}")
    if path.suffix.lower() in (".heic", ".heif"):
        raise ValueError(f"{path.name}: HEIC is not supported, convert it first: "
                         f"sips -s format jpeg in.heic --out in.jpg")
    # Phones store the sensor image unrotated and put the orientation in EXIF.
    img = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    scale = max_side / max(img.size)
    if scale < 1:
        size = (round(img.width * scale), round(img.height * scale))
        img = img.resize(size, Image.LANCZOS)
    return np.asarray(img, dtype=np.float64) / 255.0


def save_photo(path, img: np.ndarray) -> None:
    pixels = np.round(np.clip(img, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(pixels).save(path, quality=92)


# JPEG values are gamma-encoded, but blur adds up light linearly,
# so the convolution model only holds after converting to linear light.
def srgb_to_linear(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(x):
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)


def motion_psf(length: float, angle: float) -> np.ndarray:
    """Straight motion blur of `length` px, `angle` degrees counter-clockwise from horizontal.

    The segment is sampled densely and each sample is split between its 4 nearest
    pixels (bilinear weights), so fractional lengths and arbitrary angles give a
    smooth kernel instead of a jagged pixel line.
    """
    if length <= 1:
        return np.ones((1, 1))
    half = int(np.ceil(length / 2))
    psf = np.zeros((2 * half + 1, 2 * half + 1))

    n = int(np.ceil(length)) * 20
    t = ((np.arange(n) + 0.5) / n - 0.5) * length
    a = np.deg2rad(angle)
    x = half + t * np.cos(a)
    # Rows grow downwards, so a counter-clockwise angle means negative dy.
    y = half - t * np.sin(a)
    c, r = np.floor(x).astype(int), np.floor(y).astype(int)
    dx, dy = x - c, y - r
    np.add.at(psf, (r, c), (1 - dx) * (1 - dy))
    np.add.at(psf, (r, c + 1), dx * (1 - dy))
    np.add.at(psf, (r + 1, c), (1 - dx) * dy)
    np.add.at(psf, (r + 1, c + 1), dx * dy)
    return psf / psf.sum()


def defocus_psf(radius: float) -> np.ndarray:
    """Uniform disk of `radius` px; edge pixels are weighted by the covered area (8x8 supersampling)."""
    if radius <= 0.5:
        return np.ones((1, 1))
    half = int(np.ceil(radius))
    n = 2 * half + 1
    s = 8
    coords = (np.arange(n * s) + 0.5) / s - half - 0.5
    x, y = np.meshgrid(coords, coords)
    inside = (x**2 + y**2 <= radius**2).astype(float)
    psf = inside.reshape(n, s, n, s).sum(axis=(1, 3))
    return psf / psf.sum()


def psf_to_otf(psf: np.ndarray, shape) -> np.ndarray:
    """Transfer function of `psf` for an image of `shape` (same as MATLAB psf2otf)."""
    padded = np.zeros(shape)
    kh, kw = psf.shape
    padded[:kh, :kw] = psf
    # FFT convolution treats index (0, 0) as the kernel centre; without this roll
    # the result would be shifted by half a kernel.
    padded = np.roll(padded, (-(kh // 2), -(kw // 2)), axis=(0, 1))
    return fft2(padded)


def blur(img, psf):
    """Circular convolution with `psf`: the forward model that `deconvolve` inverts."""
    otf = psf_to_otf(psf, img.shape)
    return ifft2(fft2(img) * otf)


def penalty_spectrum(shape, penalty):
    """|P|^2 of the regulariser on the FFT grid."""
    if penalty == "L2":
        return np.ones(shape)
    if penalty != "H1":
        raise ValueError(f"unknown penalty {penalty!r}, expected 'L2' or 'H1'")
    # Spectrum of the discrete gradient in normalised frequencies: it lies in [0, 8]
    # for any image size, so the same mu means the same thing on every photo.
    fy = np.fft.fftfreq(shape[0])[:, None]
    fx = np.fft.fftfreq(shape[1])[None, :]
    return (2 * np.sin(np.pi * fx)) ** 2 + (2 * np.sin(np.pi * fy)) ** 2


def deconvolve(img, psf, mu: float, penalty: str = "L2") -> np.ndarray:
    """Tikhonov deconvolution of one channel: conj(K) G / (|K|^2 + mu |P|^2)."""
    otf = psf_to_otf(psf, img.shape)
    denom = np.abs(otf) ** 2 + mu * penalty_spectrum(img.shape, penalty)
    return ifft2(np.conj(otf) * fft2(img) / denom)


def grad(x):
    """Forward differences with periodic borders: the spectrum of this is penalty_spectrum("H1")."""
    return np.roll(x, -1, axis=1) - x, np.roll(x, -1, axis=0) - x


def grad_t(gx, gy):
    """Adjoint (transpose) of grad."""
    return (np.roll(gx, 1, axis=1) - gx) + (np.roll(gy, 1, axis=0) - gy)


def tv_deconvolve(img, psf, lam: float, iters: int = 50) -> np.ndarray:
    """Total-variation deconvolution of one channel: min 0.5 |k*x - g|^2 + lam * sum |grad x|.

    Solved with ADMM: z stands in for grad x, u is the scaled multiplier.
    """
    # The x step is a quadratic problem that is diagonal in Fourier, exactly like
    # Tikhonov with the H1 penalty; the z step is a per-pixel shrinkage. The L1 norm
    # of the gradient lets edges stay sharp while flat areas are smoothed.
    rho = 10 * lam
    otf = psf_to_otf(psf, img.shape)
    data = np.conj(otf) * fft2(img)
    denom = np.abs(otf) ** 2 + rho * penalty_spectrum(img.shape, "H1")
    zx = zy = ux = uy = np.zeros_like(img)
    for _ in range(iters):
        x = ifft2((data + rho * fft2(grad_t(zx - ux, zy - uy))) / denom)
        gx, gy = grad(x)
        vx, vy = gx + ux, gy + uy
        # Shorten each gradient vector by lam / rho, keeping its direction.
        shrink = np.maximum(1 - lam / (rho * np.maximum(np.hypot(vx, vy), 1e-12)), 0)
        zx, zy = shrink * vx, shrink * vy
        ux, uy = vx - zx, vy - zy
    return x


def richardson_lucy(img, psf, iters: int = 30) -> np.ndarray:
    """Richardson-Lucy deconvolution of one channel; the update keeps the image non-negative."""
    # There is no mu here: stopping early is the regularisation. More iterations
    # recover more detail but also amplify more noise.
    otf = psf_to_otf(psf, img.shape)
    img = np.maximum(img, 0)
    x = np.full_like(img, img.mean())
    for _ in range(iters):
        ratio = img / np.maximum(ifft2(fft2(x) * otf), 1e-6)
        x = x * ifft2(fft2(ratio) * np.conj(otf))
    return x


def taper_window(n, width):
    """1 in the middle, smooth (half-cosine) fall to 0 over `width` px at both ends."""
    d = np.minimum(np.arange(n), np.arange(n)[::-1])
    return np.where(d < width, 0.5 - 0.5 * np.cos(np.pi * d / width), 1.0)


def edge_taper(img, psf):
    """Blend the borders into a circularly blurred copy, like MATLAB edgetaper."""
    # Near the borders the image then looks exactly like the periodic blur the FFT
    # assumes, so the jump between opposite edges no longer causes ringing.
    w = np.outer(taper_window(img.shape[0], psf.shape[0]), taper_window(img.shape[1], psf.shape[1]))
    return w * img + (1 - w) * blur(img, psf)


def deblur_channel(img, psf, edge, solve):
    """Apply `solve` (one of the deconvolutions above) with the chosen border handling."""
    if edge == "taper":
        return solve(edge_taper(img, psf))
    # FFT treats the image as periodic; mirroring moves the left/right and top/bottom
    # mismatch out into the padding, which is cropped away afterwards.
    k = max(psf.shape)
    h, w = img.shape
    pad_h = fft.next_fast_len(h + 2 * k) - h - k
    pad_w = fft.next_fast_len(w + 2 * k) - w - k
    padded = np.pad(img, ((k, pad_h), (k, pad_w)), mode="reflect")
    return solve(padded)[k:k + h, k:k + w]


def deblur_photo(rgb: np.ndarray, psf: np.ndarray, mu: float, penalty: str = "L2",
                 edge: str = "taper", method: str = "tikhonov", lam: float = 1e-3,
                 iters: int = 30) -> np.ndarray:
    """Deblur an sRGB photo in linear light, the same kernel for every channel.

    method "tikhonov" uses mu and penalty, "tv" uses lam, "rl" (Richardson-Lucy) uses iters.
    """
    solvers = {
        "tikhonov": lambda x: deconvolve(x, psf, mu, penalty),
        "tv": lambda x: tv_deconvolve(x, psf, lam),
        "rl": lambda x: richardson_lucy(x, psf, iters),
    }
    if method not in solvers:
        raise ValueError(f"unknown method {method!r}, expected one of {list(solvers)}")
    lin = srgb_to_linear(rgb)
    channels = [deblur_channel(lin[..., c], psf, edge, solvers[method]) for c in range(3)]
    return linear_to_srgb(np.clip(np.stack(channels, axis=-1), 0, 1))


def log_spectrum(gray: np.ndarray) -> np.ndarray:
    """Log-magnitude spectrum with DC in the centre, scaled to [0, 1] for display."""
    h, w = gray.shape
    # Without the Hann window the image borders produce a bright cross through the
    # centre that hides the dark stripes left by the blur.
    window = np.outer(np.hanning(h), np.hanning(w))
    spec = np.abs(np.fft.fftshift(np.fft.fft2((gray - gray.mean()) * window)))
    spec = np.log1p(spec)
    return (spec - spec.min()) / (spec.max() - spec.min())


def make_psf(p: dict) -> np.ndarray:
    if p["kernel"] == "motion":
        return motion_psf(p["length"], p["angle"])
    return defocus_psf(p["radius"])


def scale_params(p: dict, s: float) -> dict:
    """Parameters for the same photo resized by factor s."""
    p = dict(p, length=p["length"] * s, radius=p["radius"] * s)
    # For L2 the filter only depends on |K|^2 + mu, which is resolution free.
    # For H1, |P|^2 ~ f^2 and a feature at frequency f moves to f/s, so mu * s^2
    # keeps the filter the same on the same image content.
    if p["penalty"] == "H1":
        p["mu"] = p["mu"] * s**2
    # TV: the data term sums over s^2 times more pixels, while the gradients get s
    # times smaller, so the TV term only grows by s. lam * s keeps the balance.
    if "lam" in p:
        p["lam"] = p["lam"] * s
    return p


def save_compare(path, panels, titles, caption=""):
    """Save images side by side at their native resolution with titles above and a caption below."""
    h, w = panels[0].shape[:2]
    dpi = 100
    top = 40
    # At fontsize 11 a character is up to ~8 px wide; wrap so narrow images don't cut the caption off.
    lines = textwrap.wrap(caption, max(20, len(panels) * w // 8))
    caption = "\n".join(lines)
    bottom = 20 + 18 * len(lines) if lines else 0
    fig = Figure(figsize=(len(panels) * w / dpi, (h + top + bottom) / dpi), dpi=dpi)
    total_h = h + top + bottom
    for i, (img, title) in enumerate(zip(panels, titles)):
        ax = fig.add_axes([i / len(panels), bottom / total_h, 1 / len(panels), h / total_h])
        ax.imshow(np.clip(img, 0, 1), cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        ax.set_axis_off()
        fig.text((i + 0.5) / len(panels), 1 - 0.5 * top / total_h, title,
                 ha="center", va="center", fontsize=14)
    if caption:
        fig.text(0.5, 0.5 * bottom / total_h, caption, ha="center", va="center", fontsize=11)
    fig.savefig(path, dpi=dpi, pil_kwargs={"quality": 92})
