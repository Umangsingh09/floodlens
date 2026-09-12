from __future__ import annotations

from pydantic import BaseModel


class HistoricalEvent(BaseModel):
    dfoId: int
    imageId: str
    startDate: str
    endDate: str
    primaryCountry: str
    countries: str
    resolutionMeters: float
    referenceType: str
