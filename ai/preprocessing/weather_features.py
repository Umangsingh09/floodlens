"""Real weather/hydrology inputs: antecedent rainfall and soil moisture.

Sentinel-1 backscatter change and terrain alone miss the most direct physical driver of
flooding — how much rain has actually fallen, and how saturated the ground already is before it
does. Both come from public, near-real-time Earth Engine datasets:

- Rainfall: NASA GPM IMERG (`NASA/GPM_L3/IMERG_V07`), half-hourly precipitation, ~1 day latency.
  We sum it over a lookback window to get an antecedent rainfall total, since a single half-hour
  reading says little about flood risk on its own — days of accumulated rain do.
- Soil moisture: NASA SMAP L4 (`NASA/SMAP/SPL4SMGP/008`), ~4 day latency. Surface soil moisture
  indicates how much more rain the ground can absorb before it runs off instead.

Both are much coarser than Sentinel-1 (IMERG ~11km, SMAP ~9km, vs. the 250m training grid), so
they're resampled (bilinear + reproject) onto the same grid as everything else — this is
legitimate spatial interpolation of real point/coarse-cell measurements, not fabricated data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

RAINFALL_LOOKBACK_DAYS = 7


def fetch_antecedent_rainfall(roi: Any, observation_time: datetime, *, lookback_days: int = RAINFALL_LOOKBACK_DAYS) -> Any:
    """Return total real GPM IMERG rainfall (mm) over the `lookback_days` before `observation_time`."""
    import ee  # type: ignore

    start = (observation_time - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end = (observation_time + timedelta(days=1)).strftime("%Y-%m-%d")
    collection = (
        ee.ImageCollection("NASA/GPM_L3/IMERG_V07")
        .filterBounds(roi)
        .filterDate(start, end)
        .filter(ee.Filter.lte("system:time_start", int(observation_time.timestamp() * 1000)))
        .select("precipitation")
    )
    return collection.sum().rename("rainfall_7d").clip(roi)


def fetch_soil_moisture(roi: Any, observation_time: datetime, *, max_lookback_days: int = 10) -> Any:
    """Return the most recent real SMAP L4 surface soil-moisture image at or before `observation_time`."""
    import ee  # type: ignore

    obs_ms = int(observation_time.timestamp() * 1000)
    window_start = (observation_time - timedelta(days=max_lookback_days)).strftime("%Y-%m-%d")
    collection = (
        ee.ImageCollection("NASA/SMAP/SPL4SMGP/008")
        .filterBounds(roi)
        .filterDate(window_start, (observation_time + timedelta(days=1)).strftime("%Y-%m-%d"))
        .filter(ee.Filter.lte("system:time_start", obs_ms))
        .sort("system:time_start", False)
    )
    latest = ee.Image(collection.first())
    return latest.select("sm_surface").rename("soil_moisture").clip(roi)


__all__ = ["RAINFALL_LOOKBACK_DAYS", "fetch_antecedent_rainfall", "fetch_soil_moisture"]
