"""Gallery: keep finished renders as before/after pairs."""

from uuid import uuid4

from app.errors import ConflictError, NotFoundError
from app.repositories.files import FileStorage
from app.repositories.gallery import GalleryRepository
from app.repositories.jobs import JobRepository


class GalleryService:
    def __init__(
        self, gallery: GalleryRepository, jobs: JobRepository, storage: FileStorage
    ) -> None:
        self.gallery = gallery
        self.jobs = jobs
        self.storage = storage

    def add(self, job_id: str, caption: str | None) -> dict:
        job = self.jobs.get(job_id)
        if job is None:
            raise NotFoundError("Job not found")
        # Only a finished render has a result to show.
        if job["status"] != "done":
            raise ConflictError("Job is not done yet")
        item_id = uuid4().hex
        self.gallery.create(item_id, job_id, caption)
        return self.with_urls(self.gallery.get(item_id))

    def list(self) -> list[dict]:
        return [self.with_urls(item) for item in self.gallery.list()]

    def delete(self, item_id: str) -> None:
        """Removes the gallery entry only; the photo and the result stay."""
        if not self.gallery.delete(item_id):
            raise NotFoundError("Gallery item not found")

    def with_urls(self, item: dict) -> dict:
        return {
            **item,
            "before_url": self.storage.url_for(self.storage.full_path(item["photo_id"])),
            "after_url": self.storage.url_for(self.storage.result_path(item["job_id"])),
        }
