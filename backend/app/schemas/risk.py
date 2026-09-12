from __future__ import annotations

from pydantic import BaseModel, Field


class RiskSummary(BaseModel):
    min: float = 0.0
    max: float = 1.0
    mean: float = 0.0


class RiskAlert(BaseModel):
    level: str = Field(..., description="LOW, MODERATE, HIGH, VERY_HIGH")
    threshold: float = 0.7


class RiskResponse(BaseModel):
    predictionId: str
    regionId: str = "bihar-nepal"
    hazard: str = "flood"
    risk: RiskSummary
    resolutionMeters: float
    crs: str
    satellite: str = "Sentinel-1"
    sourcePassTimestamp: str
    predictionTimestamp: str
    processingLagSeconds: int
    predictionHorizonHours: int
    modelId: str
    modelVersion: str
    alert: RiskAlert
    rasterUrl: str | None = None
