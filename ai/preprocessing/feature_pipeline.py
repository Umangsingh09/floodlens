from __future__ import annotations

from typing import Any

import numpy as np

from ai.config import AISettings, get_settings
from ai.preprocessing.dem_features import compute_dem_features
from ai.preprocessing.temporal_features import build_feature_stack
from ai.preprocessing.water_mask import compute_water_mask


def build_feature_stack_from_arrays(
    vv_t: np.ndarray,
    vh_t: np.ndarray,
    vv_t_1: np.ndarray,
    vh_t_1: np.ndarray,
    *,
    water_current: np.ndarray | None = None,
    water_previous: np.ndarray | None = None,
    water_baseline: np.ndarray | None = None,
    elevation: np.ndarray | None = None,
    slope: np.ndarray | None = None,
    fill_value: float = 0.0,
) -> dict[str, np.ndarray]:
    """Create a reusable feature stack aligned to the Sentinel-1 analysis grid."""
    features = build_feature_stack(
        vv_t,
        vh_t,
        vv_t_1,
        vh_t_1,
        fill_value=fill_value,
        water_current=water_current,
        water_previous=water_previous,
        water_baseline=water_baseline,
    )

    if elevation is not None or slope is not None:
        dem = compute_dem_features(elevation if elevation is not None else np.zeros_like(vv_t, dtype=np.float32), slope if slope is not None else np.zeros_like(vv_t, dtype=np.float32), fill_value=fill_value)
        features.update(dem)

    return features


def compute_water_mask_from_backscatter(
    backscatter: np.ndarray,
    *,
    threshold: float | None = None,
    nodata: float | None = None,
) -> np.ndarray:
    """Reusable per-image water mask for the SAR stack."""
    return compute_water_mask(backscatter, threshold=threshold, nodata=nodata)


def get_default_feature_names() -> list[str]:
    return [
        "vv_t",
        "vh_t",
        "vv_t_1",
        "vh_t_1",
        "delta_vv",
        "delta_vh",
        "water_current",
        "water_previous",
        "water_change",
        "water_persistence",
        "water_baseline",
        "water_trend",
        "elevation",
        "slope",
    ]


def get_feature_pipeline_config(settings: AISettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    return {
        "region_name": settings.region_name,
        "aoi_name": settings.aoi_name,
        "start_date": settings.start_date,
        "end_date": settings.end_date,
        "instrument_mode": settings.instrument_mode,
        "polarizations": list(settings.polarizations),
        "water_threshold_db": settings.water_threshold_db,
        "dem_enabled": settings.dem_enabled,
        "feature_names": get_default_feature_names(),
    }
