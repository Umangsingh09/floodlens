from __future__ import annotations

import json

import numpy as np
import pytest

from ai.config import get_settings
from ai.preprocessing.feature_pipeline import build_feature_stack_from_arrays, get_default_feature_names
from ai.preprocessing.sentinel1 import align_image_to_reference_grid
from ai.preprocessing.water_mask import compute_water_mask


def _safe_initialize_gee():
    ee = pytest.importorskip(
        "ee",
        reason="Earth Engine is not installed in the active Python environment; the Phase 2 GEE integration test requires the project .venv.",
    )

    settings = get_settings()
    project_id = settings.earthengine_project or "floodlens-508418"
    try:
        ee.Initialize(project=project_id)
    except Exception:
        try:
            ee.Initialize()
        except Exception as exc:  # pragma: no cover - environment-dependent auth issue
            pytest.skip(f"Earth Engine is not authenticated in this environment: {exc}")
    return ee


def _load_aoi() -> dict:
    settings = get_settings()
    return json.loads(settings.aoi_geojson)


def _get_sample_region(ee_module) -> ee_module.Geometry:
    return ee_module.Geometry.BBox(84.80, 26.00, 84.82, 26.02).transform("EPSG:32645", maxError=1)


def test_real_phase2_feature_pipeline_small_window():
    ee = _safe_initialize_gee()
    settings = get_settings()
    region = ee.Geometry(_load_aoi())
    sample_region = _get_sample_region(ee)

    start_date = "2024-09-01"
    end_date = "2024-09-30"
    collection = (
        ee.ImageCollection(settings.satellite_collection)
        .filterBounds(region)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.eq("instrumentMode", settings.instrument_mode))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .sort("system:time_start")
    )

    scene_count = int(collection.size().getInfo())
    assert scene_count >= 2, f"Expected at least two Sentinel-1 scenes in {start_date} to {end_date}, found {scene_count}."

    image_pair = collection.limit(2).toList(2)
    current_image = ee.Image(image_pair.get(0))
    previous_image = ee.Image(image_pair.get(1))

    current_image = align_image_to_reference_grid(current_image, sample_region, crs="EPSG:32645", scale=10.0)
    previous_image = align_image_to_reference_grid(previous_image, sample_region, crs="EPSG:32645", scale=10.0)

    vv_current = np.asarray(current_image.select("VV").sampleRectangle(sample_region, defaultValue=0).get("VV").getInfo(), dtype=np.float32)
    vh_current = np.asarray(current_image.select("VH").sampleRectangle(sample_region, defaultValue=0).get("VH").getInfo(), dtype=np.float32)
    vv_previous = np.asarray(previous_image.select("VV").sampleRectangle(sample_region, defaultValue=0).get("VV").getInfo(), dtype=np.float32)
    vh_previous = np.asarray(previous_image.select("VH").sampleRectangle(sample_region, defaultValue=0).get("VH").getInfo(), dtype=np.float32)

    assert vv_current.shape == vh_current.shape == vv_previous.shape == vh_previous.shape
    assert vv_current.size > 0
    assert np.isfinite(vv_current).any()

    water_current = compute_water_mask(vv_current, threshold=settings.water_threshold_db)
    water_previous = compute_water_mask(vv_previous, threshold=settings.water_threshold_db)
    water_baseline = np.zeros_like(water_current, dtype=bool)

    dem_image = ee.Image(settings.dem_dataset).select("elevation")
    slope_image = ee.Terrain.slope(dem_image)
    elevation = np.asarray(dem_image.sampleRectangle(sample_region, defaultValue=0).get("elevation").getInfo(), dtype=np.float32)
    slope = np.asarray(slope_image.sampleRectangle(sample_region, defaultValue=0).get("slope").getInfo(), dtype=np.float32)

    assert elevation.shape == slope.shape
    assert np.isfinite(elevation).any()
    assert np.isfinite(slope).any()

    feature_stack = build_feature_stack_from_arrays(
        vv_current,
        vh_current,
        vv_previous,
        vh_previous,
        water_current=water_current.astype(np.float32),
        water_previous=water_previous.astype(np.float32),
        water_baseline=water_baseline.astype(np.float32),
        elevation=elevation,
        slope=slope,
        fill_value=0.0,
    )

    required_core_features = {
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
    }

    assert set(feature_stack.keys()) == required_core_features, f"Unexpected feature stack: {sorted(feature_stack.keys())}"
    assert all(feature_stack[name].shape == vv_current.shape for name in required_core_features if name in {"vv_t", "vh_t", "vv_t_1", "vh_t_1", "water_current", "water_previous", "water_change", "water_persistence", "water_trend"})
    assert feature_stack["elevation"].shape == elevation.shape
    assert feature_stack["slope"].shape == slope.shape
    assert np.isfinite(feature_stack["delta_vv"]).all()
    assert np.isfinite(feature_stack["delta_vh"]).all()
    assert np.isfinite(feature_stack["elevation"]).all()
    assert np.isfinite(feature_stack["slope"]).all()

    assert get_default_feature_names() == [
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
        "rainfall_7d",
        "soil_moisture",
    ]

    print({
        "scene_count": scene_count,
        "date_range": {"start": start_date, "end": end_date},
        "aoi": "bihar-nepal",
        "sample_region": [84.80, 26.00, 84.82, 26.02],
        "features": sorted(feature_stack.keys()),
    })
