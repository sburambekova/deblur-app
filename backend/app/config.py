"""Application settings, read from DEBLUR_* environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DEBLUR_")

    data_dir: Path = Path("data")
    max_upload_mb: int = 15
    full_side: int = 1600
    preview_side: int = 512
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    @property
    def db_path(self) -> Path:
        return self.data_dir / "deblur.sqlite3"

    @property
    def files_dir(self) -> Path:
        """The only folder served as /files/..."""
        return self.data_dir / "files"
