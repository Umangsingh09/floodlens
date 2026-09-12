from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from ai.config import AISettings, get_settings


@dataclass(frozen=True)
class Sentinel1PreprocessingConfig:
    """Configuration for processing real Sentinel-1 acquisitions."""

    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    aoi_geojson: str | None = None
    instrument_mode: str = "IW"
    polarization: str = "VV"
    polarizations: tuple[str, ...] = ("VV", "VH")
    water_threshold_db: float = -12.0
    nodata_value: float | None = None
    use_dem: bool = True

    @classmethod
    def from_settings(cls, settings: AISettings | None = None) -> "Sentinel1PreprocessingConfig":
        settings = settings or get_settings()
        return cls(
            start_date=settings.start_date,
            end_date=settings.end_date,
            aoi_geojson=settings.aoi_geojson,
            instrument_mode=settings.instrument_mode,
            polarizations=settings.polarizations,
            water_threshold_db=settings.water_threshold_db,
            use_dem=settings.dem_enabled,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "aoi_geojson": json.loads(self.aoi_geojson) if self.aoi_geojson else None,
            "instrument_mode": self.instrument_mode,
            "polarization": self.polarization,
            "polarizations": list(self.polarizations),
            "water_threshold_db": self.water_threshold_db,
            "nodata_value": self.nodata_value,
            "use_dem": self.use_dem,
        }
