from __future__ import annotations

from pydantic import BaseModel, Field


class RiskSummary(BaseModel):
    min: float = 0.0
    max: float = 1.0
    mean: float = 0.0


class RiskAlert(BaseModel):
    level: str = Field(..., description="LOW, MODERATE, HIGH, VERY_HIGH")
    threshold: float = 0.7


class RiskBounds(BaseModel):
    west: float
    south: float
    east: float
    north: float


class RiskResponse(BaseModel):
    predictionId: str
    regionId: str = "bihar-nepal"
    hazard: str = "flood"
    risk: RiskSummary
    resolutionMeters: float
    crs: str
    bounds: RiskBounds | None = None
    satellite: str = "Sentinel-1"
    sourcePassTimestamp: str
    predictionTimestamp: str
    processingLagSeconds: int
    predictionHorizonHours: int
    modelId: str
    modelVersion: str
    alert: RiskAlert
    rasterUrl: str | None = None
    previewUrl: str | None = None
    gridUrl: str | None = None
    observationWindowScenes: list[str] | None = None
    gridShape: list[int] | None = None


class RiskHistoryPoint(BaseModel):
    predictionId: str
    predictionTimestamp: str
    mean: float
    alertLevel: str


class RiskGridCell(BaseModel):
    lat: float
    lon: float
    value: float


class RiskGridResponse(BaseModel):
    rows: int
    cols: int
    cells: list[RiskGridCell]
