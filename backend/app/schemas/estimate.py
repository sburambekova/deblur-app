from typing import Literal

from pydantic import BaseModel, Field


class EstimateIn(BaseModel):
    kernel: Literal["motion", "defocus"] = Field("motion", description="Blur type to estimate.")


# Same units and ranges as DeblurParams. Only the fields of the estimated kernel are set.
class EstimateOut(BaseModel):
    kernel: Literal["motion", "defocus"]
    length: float | None = None
    angle: float | None = None
    radius: float | None = None
