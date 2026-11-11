"""Files on disk: where each image lives and how numpy arrays become image files and back."""

from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image


def to_uint8(img: np.ndarray) -> np.ndarray:
    return np.round(np.clip(img, 0, 1) * 255).astype(np.uint8)


class FileStorage:
    """Everything under files_dir is served as /files/..., so only images go here."""

    def __init__(self, files_dir: Path) -> None:
        self.files_dir = files_dir

    def photo_dir(self, photo_id: str) -> Path:
        return self.files_dir / "photos" / photo_id

    def full_path(self, photo_id: str) -> Path:
        return self.photo_dir(photo_id) / "full.png"

    def preview_path(self, photo_id: str) -> Path:
        return self.photo_dir(photo_id) / "preview.png"

    def spectrum_path(self, photo_id: str) -> Path:
        return self.photo_dir(photo_id) / "spectrum.png"

    def result_path(self, job_id: str) -> Path:
        return self.files_dir / "results" / f"{job_id}.jpg"

    def url_for(self, path: Path) -> str:
        return "/files/" + path.relative_to(self.files_dir).as_posix()

    def read_rgb(self, path: Path) -> np.ndarray:
        """RGB image as float64 in [0, 1], H x W x 3."""
        with Image.open(path) as img:
            return np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0

    def write_png(self, path: Path, img: np.ndarray) -> None:
        """Save an RGB (H x W x 3) or gray (H x W) image with values in [0, 1]."""
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.fromarray(to_uint8(img)).save(path)

    def write_jpeg(self, path: Path, rgb: np.ndarray, quality: int) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.encode_jpeg(rgb, quality))

    def encode_jpeg(self, rgb: np.ndarray, quality: int) -> bytes:
        """JPEG file contents in memory, for responses that are not stored."""
        buf = BytesIO()
        Image.fromarray(to_uint8(rgb)).save(buf, "JPEG", quality=quality)
        return buf.getvalue()
