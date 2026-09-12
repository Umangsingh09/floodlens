from __future__ import annotations

import json
from typing import Any

from app.schemas.region import RegionBounds, RegionResponse


def _compute_bounds(geojson: dict[str, Any]) -> RegionBounds:
    coordinates = geojson["coordinates"][0]
    lons = [pt[0] for pt in coordinates]
    lats = [pt[1] for pt in coordinates]
    return RegionBounds(west=min(lons), south=min(lats), east=max(lons), north=max(lats))


def get_region_info() -> RegionResponse:
    from ai.config import get_settings

    settings = get_settings()
    geojson = json.loads(settings.aoi_geojson)

    return RegionResponse(
        regionId=settings.region_name,
        aoiName=settings.aoi_name,
        geojson=geojson,
        bounds=_compute_bounds(geojson),
        satelliteCollection=settings.satellite_collection,
        predictionHorizonDays=settings.prediction_horizon_days,
    )
