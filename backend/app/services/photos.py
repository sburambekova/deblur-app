"""Photo upload: check the file, turn it into the working images, remember the photo."""

from datetime import UTC, datetime
from io import BytesIO
from uuid import uuid4

import numpy as np
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener

from app.config import Settings
from app.engine import spectrum
from app.errors import InvalidInputError, NotFoundError, TooLargeError
from app.repositories.files import FileStorage
from app.repositories.photos import PhotoRepository

# Lets Pillow open HEIC, the default photo format of iPhones.
register_heif_opener()

# The largest kernel in the API is 61 px, and the engine needs the image to be larger than it.
MIN_PREVIEW_SIDE = 64
SPECTRUM_SIZE = 256


def shrink(img: Image.Image, side: int) -> Image.Image:
    """Resize so that the larger side is at most `side`; smaller images stay as they are."""
    scale = side / max(img.size)
    if scale >= 1:
        return img
    size = (round(img.width * scale), round(img.height * scale))
    return img.resize(size, Image.Resampling.LANCZOS)


def to_array(img: Image.Image) -> np.ndarray:
    return np.asarray(img, dtype=np.float64) / 255.0


class PhotoService:
    def __init__(self, settings: Settings, photos: PhotoRepository, storage: FileStorage) -> None:
        self.settings = settings
        self.photos = photos
        self.storage = storage
        self.max_bytes = settings.max_upload_mb * 1024 * 1024

    def upload(self, data: bytes) -> dict:
        if len(data) > self.max_bytes:
            raise TooLargeError(f"File is larger than {self.settings.max_upload_mb} MB")
        try:
            img = Image.open(BytesIO(data))
            # open() only reads the header; a truncated file fails only when it is decoded.
            img.load()
        # DecompressionBombError (an image of hundreds of megapixels) is not an OSError.
        except (OSError, Image.DecompressionBombError) as exc:
            raise InvalidInputError("Not a valid image") from exc

        img = ImageOps.exif_transpose(img).convert("RGB")
        full = shrink(img, self.settings.full_side)
        preview = shrink(full, self.settings.preview_side)
        if min(preview.size) < MIN_PREVIEW_SIDE:
            raise InvalidInputError("Image is too small or too narrow")

        photo_id = uuid4().hex
        preview_rgb = to_array(preview)
        # PNG, not JPEG: every JPEG re-save adds artifacts that deblurring then amplifies.
        self.storage.write_png(self.storage.full_path(photo_id), to_array(full))
        self.storage.write_png(self.storage.preview_path(photo_id), preview_rgb)
        self.storage.write_png(self.storage.spectrum_path(photo_id), square_spectrum(preview_rgb))

        photo = {
            "id": photo_id,
            "width": full.width,
            "height": full.height,
            "preview_width": preview.width,
            "preview_height": preview.height,
            "created_at": datetime.now(UTC).isoformat(),
        }
        self.photos.create(photo)
        return self.with_urls(photo)

    def get(self, photo_id: str) -> dict:
        photo = self.photos.get(photo_id)
        if photo is None:
            raise NotFoundError("Photo not found")
        return self.with_urls(photo)

    def with_urls(self, photo: dict) -> dict:
        url = self.storage.url_for
        return {
            **photo,
            "full_url": url(self.storage.full_path(photo["id"])),
            "preview_url": url(self.storage.preview_path(photo["id"])),
            "spectrum_url": url(self.storage.spectrum_path(photo["id"])),
        }


def square_spectrum(rgb: np.ndarray) -> np.ndarray:
    """Log spectrum stretched to a square, so that angles in it match angles in the photo."""
    spec = spectrum.log_spectrum(spectrum.to_gray(rgb)).astype(np.float32)
    # On an H x W spectrum one pixel is 1/W of frequency across and 1/H down, so a 45 degree
    # blur on a 512 x 384 preview shows up at 37 degrees. In a square both axes are equal.
    square = Image.fromarray(spec).resize((SPECTRUM_SIZE, SPECTRUM_SIZE), Image.Resampling.BILINEAR)
    return np.asarray(square, dtype=np.float64)
