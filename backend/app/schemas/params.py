"""Deblur parameters. All lengths are in preview pixels (larger side 512)."""

from typing import Literal

from pydantic import BaseModel, Field


# Ranges are checked by Pydantic, so FastAPI rejects bad values with 422 by itself.
class DeblurParams(BaseModel):
    kernel: Literal["motion", "defocus"] = "motion"
    length: float = Field(15, ge=1, le=60, description="Motion length, px. Used by motion.")
    angle: float = Field(
        0, ge=0, le=180, description="Motion direction, degrees counter-clockwise from horizontal."
    )
    radius: float = Field(3, ge=0.5, le=25, description="Defocus radius, px. Used by defocus.")
    method: Literal["tikhonov", "tv", "rl"] = Field(
        "rl", description="Method for /render. /preview always uses tikhonov."
    )
    # Above 0.1 Tikhonov with L2 visibly darkens the image: the gain at zero frequency is 1/(1+mu).
    mu: float = Field(0.01, ge=1e-6, le=0.1, description="Used by tikhonov and /preview.")
    penalty: Literal["L2", "H1"] = Field("L2", description="Used by tikhonov and /preview.")
    lam: float = Field(5e-4, ge=1e-6, le=0.1, description="Used by tv.")
    iters: int = Field(80, ge=1, le=200, description="Used by rl.")
