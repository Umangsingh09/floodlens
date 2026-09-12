from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class RegionBounds(BaseModel):
    west: float
    south: float
    east: float
    north: float


class RegionResponse(BaseModel):
    regionId: str
    aoiName: str
    geojson: dict[str, Any]
    bounds: RegionBounds
    satelliteCollection: str
    predictionHorizonDays: int
