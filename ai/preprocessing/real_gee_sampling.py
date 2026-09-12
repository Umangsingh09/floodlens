from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from ai.config import get_settings
from ai.historical_reference import GFD_REFERENCE_RESOLUTION_M, build_gfd_flood_reference
from ai.preprocessing.sentinel1 import align_image_to_reference_grid, get_reference_projection
from ai.preprocessing.temporal_features import build_feature_stack
from ai.preprocessing.water_mask import compute_water_mask

DEFAULT_TRAINING_GRID_CRS = "EPSG:32645"
DEFAULT_TRAINING_GRID_SCALE_M = 250.0
DEFAULT_SENTINEL_GRID_SCALE_M = 10.0
DEFAULT_PREDICTION_HORIZON_DAYS = 7
DEFAULT_OBSERVATION_WINDOW_DAYS = (-2, 0)


@dataclass(frozen=True)
class GridSpec:
    """Explicit training grid for FloodLens feature/label alignment.

    The future-flood model uses a deterministic grid in the local UTM CRS so that all
    multiscale Sentinel-1 features and the GFD historical reference share a common spatial
    coordinate system. The GFD product is still a 250 m MODIS-derived historical reference,
    not ground truth, so the training grid preserves the 250 m target resolution.
    """

    crs: str = DEFAULT_TRAINING_GRID_CRS
    scale_m: float = DEFAULT_TRAINING_GRID_SCALE_M
    feature_scale_m: float = DEFAULT_SENTINEL_GRID_SCALE_M
    label_scale_m: float = GFD_REFERENCE_RESOLUTION_M
    max_pixels: int = 1_000_000


@dataclass(frozen=True)
class SamplingDiagnostics:
    selected_scene_ids: tuple[str, ...]
    selected_scene_timestamps: tuple[str, ...]
    t_scene_id: str | None
    t_minus_1_scene_id: str | None
    t_minus_2_scene_id: str | None
    observation_timestamp: str
    target_timestamp: str
    crs: str
    feature_grid_scale_m: float
    label_grid_scale_m: float
    feature_dimensions: tuple[int, int]
    label_dimensions: tuple[int, int]
    valid_cells: int
    flood_reference_cells: int
    flood_reference_percentage: float
    permanent_water_excluded: int
    nan_count: int
    inf_count: int
    feature_ranges: dict[str, tuple[float, float]]
    label_unique_values: tuple[int, ...]
    spatial_alignment_confirmed: bool


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, np.datetime64):
        return datetime.fromisoformat(str(value))
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Unsupported timestamp type: {type(value)!r}")


def _as_utc_ms(value: Any) -> int:
    import ee  # type: ignore

    if isinstance(value, ee.Date):
        return int(value.millis().getInfo())
    dt = _as_datetime(value)
    return int(dt.timestamp() * 1000)


def _aggregate_block_mean(array: np.ndarray, block_h: int, block_w: int) -> np.ndarray:
    arr = np.asarray(array, dtype=np.float32)
    if arr.ndim != 2:
        raise ValueError(f"Expected 2D array for aggregation, got {arr.shape!r}.")
    if block_h <= 1 and block_w <= 1:
        return arr
    h, w = arr.shape
    pad_h = (block_h - (h % block_h)) % block_h
    pad_w = (block_w - (w % block_w)) % block_w
    if pad_h or pad_w:
        arr = np.pad(arr, ((0, pad_h), (0, pad_w)), mode="constant", constant_values=np.nan)
    h2, w2 = arr.shape
    out = arr.reshape(h2 // block_h, block_h, w2 // block_w, block_w).mean(axis=(1, 3))
    return out.astype(np.float32)


def aggregate_feature_to_label_grid(
    feature: np.ndarray,
    *,
    block_h: int = 1,
    block_w: int = 1,
    method: str = "mean",
) -> np.ndarray:
    """Aggregate a 10 m Sentinel-1 feature to the 250 m training grid.

    For continuous SAR and DEM features, the aggregation method is the arithmetic mean across
    each 250 m cell because it preserves the expected backscatter and terrain value over the area
    while limiting the impact of a few extreme 10 m pixels. For binary water indicators, we also
    take the mean and interpret it as the fractional water cover within the cell. This creates a
    deterministic, spatially aligned representation that is physically interpretable at the 250 m
    reference scale.
    """
    array = np.asarray(feature, dtype=np.float32)
    if method != "mean":
        raise ValueError("Only mean aggregation is supported for the FloodLens training grid.")
    if block_h == 1 and block_w == 1:
        return array
    return _aggregate_block_mean(array, block_h, block_w)


def _ee_observation_window(
    collection: Any,
    observation_time: Any,
    *,
    count: int = 3,
    max_lookback_days: int = 30,
) -> list[dict[str, Any]]:
    import ee  # type: ignore

    obs_ms = _as_utc_ms(observation_time)
    current = collection.filter(ee.Filter.lte("system:time_start", obs_ms)).sort("system:time_start", False)
    scene_list = current.limit(count).getInfo().get("features", [])
    if len(scene_list) < count:
        raise ValueError(
            f"Expected at least {count} Sentinel-1 scenes on or before {observation_time}, found {len(scene_list)}."
        )

    selected: list[dict[str, Any]] = []
    for feature in scene_list:
        props = feature.get("properties", {})
        timestamp = props.get("system:time_start")
        if timestamp is None:
            continue
        dt = datetime.fromtimestamp(int(timestamp) / 1000.0)
        delta_days = (datetime.fromtimestamp(obs_ms / 1000.0) - dt).total_seconds() / 86400.0
        if delta_days <= max_lookback_days:
            selected.append({"id": props.get("system:index"), "timestamp": timestamp})
    if len(selected) < count:
        raise ValueError(
            f"Selected fewer than {count} valid scenes within the lookback window for observation time {observation_time}."
        )
    return selected[:count]


def _has_real_signal(vv: np.ndarray | Any, vh: np.ndarray | Any, *, min_magnitude: float = 1e-6) -> bool:
    """Return True only when a scalar SAR sample contains actual signal instead of all-zero/no-data fill values."""
    arrays = [np.asarray(vv, dtype=np.float32), np.asarray(vh, dtype=np.float32)]
    magnitudes: list[float] = []
    for array in arrays:
        if array.size == 0:
            continue
        finite = np.isfinite(array)
        if not np.any(finite):
            continue
        magnitudes.append(float(np.nanmax(np.abs(array[finite]))))
    if not magnitudes:
        return False
    return max(magnitudes) > min_magnitude


def select_temporal_observation_scenes(
    scene_timestamps: Sequence[Any],
    observation_time: Any,
    *,
    count: int = 3,
    max_lookback_days: int = 30,
    signal_presence: Sequence[bool] | None = None,
) -> list[datetime]:
    """Select up to `count` unique acquisition dates on or before the observation timestamp.

    Sentinel-1 collections can contain multiple granule acquisitions on the same calendar day.
    Those duplicates must collapse to a single unique observation date before constructing the
    temporal features for t, t-1 and t-2. This prevents a same-day duplicate from creating a
    false historical previous observation and zeroing out the real prior feature values.

    A scene that has no real SAR signal in the analysis ROI (for example, zero-filled values because
    the geometry does not intersect the ROI or the image is entirely missing) is treated as invalid and
    excluded so the temporal stack cannot silently collapse to zeros.
    """
    if signal_presence is not None and len(signal_presence) != len(scene_timestamps):
        raise ValueError("signal_presence must match scene_timestamps in length.")

    obs_dt = _as_datetime(observation_time)
    latest_by_day: dict[str, datetime] = {}
    for idx, ts in enumerate(scene_timestamps):
        if signal_presence is not None and not signal_presence[idx]:
            continue
        dt = _as_datetime(ts)
        if dt > obs_dt:
            continue
        delta = obs_dt - dt
        if delta.days > max_lookback_days:
            continue
        day_key = dt.date().isoformat()
        if day_key not in latest_by_day or dt > latest_by_day[day_key]:
            latest_by_day[day_key] = dt

    selected = sorted(latest_by_day.values())
    survivors = selected[-count:]
    if len(survivors) < count:
        raise ValueError(
            f"Insufficient valid unique acquisition dates before observation timestamp {obs_dt.isoformat()}; "
            f"found {len(survivors)} when {count} were required."
        )
    return survivors


def _ensure_matching_grid(feature_map: Mapping[str, np.ndarray], label: np.ndarray) -> tuple[dict[str, np.ndarray], np.ndarray]:
    label_shape = tuple(np.asarray(label, dtype=np.bool_).shape)
    aligned_map: dict[str, np.ndarray] = {}
    for key, value in feature_map.items():
        array = np.asarray(value, dtype=np.float32)
        if array.shape != label_shape:
            raise ValueError(f"Feature '{key}' grid shape {array.shape} does not match label grid shape {label_shape}.")
        aligned_map[key] = array
    return aligned_map, np.asarray(label, dtype=np.bool_)


def _count_invalid_values(array: np.ndarray) -> tuple[int, int]:
    arr = np.asarray(array, dtype=np.float32)
    return int(np.count_nonzero(~np.isfinite(arr))), int(np.count_nonzero(np.isinf(arr)))


def _estimate_sample_pixels(roi: Any, *, crs: str, scale_m: float) -> int:
    """Estimate the number of pixels the ROI would require at the target training scale.

    This is a pre-flight safety check: Earth Engine rejects huge sampleRectangle requests even when
    the ROI is conceptually small in geographic terms. By bounding the ROI in the target CRS and
    dividing by the training-grid scale, we can fail early with a clear message instead of sending a
    massive request to the server.
    """
    import ee  # type: ignore

    geometry = ee.Geometry(roi).transform(crs, maxError=1)
    coords = ee.List(geometry.coordinates().get(0))
    xs = ee.List(coords.map(lambda point: ee.List(point).get(0)))
    ys = ee.List(coords.map(lambda point: ee.List(point).get(1)))
    min_x = ee.Number(xs.reduce(ee.Reducer.min()))
    max_x = ee.Number(xs.reduce(ee.Reducer.max()))
    min_y = ee.Number(ys.reduce(ee.Reducer.min()))
    max_y = ee.Number(ys.reduce(ee.Reducer.max()))
    width_m = max_x.subtract(min_x).abs()
    height_m = max_y.subtract(min_y).abs()
    columns = width_m.divide(scale_m).ceil()
    rows = height_m.divide(scale_m).ceil()
    return int(columns.multiply(rows).getInfo())


def _sample_ee_image_to_2d(image: Any, roi: Any, *, band: str, default_value: float = 0.0) -> np.ndarray:
    import ee  # type: ignore

    sample = ee.Image(image).select(band).sampleRectangle(roi, defaultValue=default_value)
    return np.asarray(sample.get(band).getInfo(), dtype=np.float32)


def _aggregate_ee_image_to_training_grid(image: Any, roi: Any, *, crs: str, scale_m: float, reducer: str = "mean") -> Any:
    """Aggregate an Earth Engine image to the explicit 250 m training grid before sampling."""
    import ee  # type: ignore

    projection = ee.Projection(crs).atScale(scale_m)
    max_pixels = 65_535
    if reducer == "mean":
        reduced = ee.Image(image).reduceResolution(reducer=ee.Reducer.mean(), maxPixels=max_pixels, bestEffort=True)
    elif reducer == "mode":
        reduced = ee.Image(image).reduceResolution(reducer=ee.Reducer.mode(), maxPixels=max_pixels, bestEffort=True)
    else:
        raise ValueError(f"Unsupported aggregation reducer: {reducer!r}")
    return reduced.reproject(projection).clip(roi)


def _compute_training_label(
    flood_reference: np.ndarray,
    permanent_water: np.ndarray,
    *,
    nodata: float | None = None,
) -> tuple[np.ndarray, int]:
    reference = build_gfd_flood_reference(
        np.asarray(flood_reference, dtype=np.float32),
        np.asarray(permanent_water, dtype=np.float32),
        nodata=nodata,
    )
    excluded = int(np.count_nonzero(np.asarray(permanent_water, dtype=np.float32) == 1.0))
    return np.asarray(reference, dtype=np.bool_), excluded


def build_real_training_sample(
    aoi_geometry: Any,
    observation_timestamp: Any,
    *,
    settings: Any | None = None,
    sample_region: Any | None = None,
    grid_spec: GridSpec | None = None,
    min_scene_count: int = 3,
    max_lookback_days: int = 30,
    gfd_start_date: str = "2017-08-10",
    gfd_end_date: str = "2017-08-27",
) -> tuple[dict[str, np.ndarray], np.ndarray, dict[str, Any]]:
    """Build a small, leakage-safe real Earth Engine training sample.

    The sample intentionally uses a tiny ROI and a short historical validation period, and it
    validates the real data contract before larger production exports are attempted. The feature
    arrays are built from Sentinel-1 scenes on or before the observation timestamp only; the label
    is created from the future GFD reference at t+7 and is aligned to the same 250 m grid.
    """
    import ee  # type: ignore

    settings = settings or get_settings()
    grid = grid_spec or GridSpec()
    roi = ee.Geometry(aoi_geometry)
    sample_roi = ee.Geometry(sample_region) if sample_region is not None else roi
    target_roi = sample_roi.transform(grid.crs, maxError=1)
    training_projection = ee.Projection(grid.crs).atScale(grid.scale_m)

    estimated_pixels = _estimate_sample_pixels(target_roi, crs=grid.crs, scale_m=grid.scale_m)
    if estimated_pixels > 262_144:
        raise ValueError(
            f"Requested 250 m sampling grid would exceed Earth Engine sampleRectangle limit: {estimated_pixels} pixels "
            f"for ROI {sample_roi.bounds().getInfo()} at {grid.scale_m} m. Use a smaller ROI."
        )

    collection = (
        ee.ImageCollection(settings.satellite_collection)
        .filterBounds(roi)
        .filterDate("2017-08-01", "2017-08-30")
        .filter(ee.Filter.eq("instrumentMode", settings.instrument_mode))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .sort("system:time_start")
    )

    obs_dt = _as_datetime(observation_timestamp)
    obs_ms = _as_utc_ms(obs_dt)
    valid_collection = collection.filter(ee.Filter.lte("system:time_start", obs_ms)).sort("system:time_start", False)
    selected = valid_collection.limit(max(min_scene_count * 4, min_scene_count + 6)).getInfo().get("features", [])
    if len(selected) < min_scene_count:
        raise ValueError(
            f"Need at least {min_scene_count} Sentinel-1 scenes before observation {obs_dt.isoformat()}, found {len(selected)}."
        )

    candidate_scene_info: list[dict[str, Any]] = []
    for feature in selected:
        properties = feature.get("properties", {})
        scene_id = properties.get("system:index")
        timestamp = properties.get("system:time_start")
        if scene_id is None or timestamp is None:
            continue
        dt = datetime.fromtimestamp(int(timestamp) / 1000.0)
        if dt > obs_dt:
            continue
        scene_image = ee.Image(ee.ImageCollection(settings.satellite_collection).filter(ee.Filter.eq("system:index", scene_id)).first())
        scene_geometry = ee.Geometry(scene_image.geometry())
        if not scene_geometry.intersects(sample_roi).getInfo():
            continue
        vv_values = np.asarray(scene_image.select("VV").sampleRectangle(sample_roi, defaultValue=0).get("VV").getInfo(), dtype=np.float32)
        vh_values = np.asarray(scene_image.select("VH").sampleRectangle(sample_roi, defaultValue=0).get("VH").getInfo(), dtype=np.float32)
        has_real_signal = _has_real_signal(vv_values, vh_values)
        if not has_real_signal:
            continue
        candidate_scene_info.append({
            "id": str(scene_id),
            "timestamp": datetime.fromtimestamp(int(timestamp) / 1000.0).isoformat(),
            "dt": dt,
        })

    if len(candidate_scene_info) < min_scene_count:
        raise ValueError(
            f"Need at least {min_scene_count} Sentinel-1 scenes with real signal before observation {obs_dt.isoformat()} in the sample ROI, "
            f"but found {len(candidate_scene_info)}."
        )

    latest_by_day: dict[str, dict[str, Any]] = {}
    for item in candidate_scene_info:
        day_key = item["dt"].date().isoformat()
        if day_key not in latest_by_day or item["dt"] > _as_datetime(latest_by_day[day_key]["timestamp"]):
            latest_by_day[day_key] = {"id": item["id"], "timestamp": item["timestamp"]}

    ordered_unique = sorted(latest_by_day.values(), key=lambda item: _as_datetime(item["timestamp"]))
    selected_unique = ordered_unique[-min_scene_count:]
    if len(selected_unique) < min_scene_count:
        raise ValueError(
            f"Need at least {min_scene_count} unique acquisition dates before observation {obs_dt.isoformat()} but found {len(selected_unique)}."
        )

    scene_ids: list[str] = [str(item["id"]) for item in selected_unique]
    scene_timestamps: list[int] = [
        int(_as_datetime(item["timestamp"]).timestamp() * 1000.0) for item in selected_unique
    ]

    if any(ts > obs_ms for ts in scene_timestamps):
        raise ValueError("Leakage detected: a future scene was selected for the observation window.")

    target_dt = obs_dt + timedelta(days=DEFAULT_PREDICTION_HORIZON_DAYS)
    scene_images = [ee.Image(ee.ImageCollection(settings.satellite_collection).filter(ee.Filter.eq("system:index", scene_id)).first()) for scene_id in scene_ids]
    aligned = [align_image_to_reference_grid(image, sample_roi, crs=grid.crs, scale=grid.feature_scale_m) for image in scene_images]

    vv_t = _aggregate_ee_image_to_training_grid(aligned[0].select("VV"), target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    vh_t = _aggregate_ee_image_to_training_grid(aligned[0].select("VH"), target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    vv_t_1 = _aggregate_ee_image_to_training_grid(aligned[1].select("VV"), target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    vh_t_1 = _aggregate_ee_image_to_training_grid(aligned[1].select("VH"), target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    vv_t_2 = _aggregate_ee_image_to_training_grid(aligned[2].select("VV"), target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    vh_t_2 = _aggregate_ee_image_to_training_grid(aligned[2].select("VH"), target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")

    vv_t_arr = _sample_ee_image_to_2d(vv_t, target_roi, band="VV").astype(np.float32)
    vh_t_arr = _sample_ee_image_to_2d(vh_t, target_roi, band="VH").astype(np.float32)
    vv_t_1_arr = _sample_ee_image_to_2d(vv_t_1, target_roi, band="VV").astype(np.float32)
    vh_t_1_arr = _sample_ee_image_to_2d(vh_t_1, target_roi, band="VH").astype(np.float32)
    vv_t_2_arr = _sample_ee_image_to_2d(vv_t_2, target_roi, band="VV").astype(np.float32)
    vh_t_2_arr = _sample_ee_image_to_2d(vh_t_2, target_roi, band="VH").astype(np.float32)

    if vv_t_arr.shape != vh_t_arr.shape or vv_t_1_arr.shape != vh_t_1_arr.shape or vv_t_2_arr.shape != vh_t_2_arr.shape:
        raise ValueError("Sentinel-1 feature shapes are inconsistent across the observation window.")

    water_current = compute_water_mask(vv_t_arr, threshold=settings.water_threshold_db)
    water_previous = compute_water_mask(vv_t_1_arr, threshold=settings.water_threshold_db)
    water_baseline = compute_water_mask(vv_t_2_arr, threshold=settings.water_threshold_db)

    dem = ee.Image(settings.dem_dataset).select("elevation")
    dem_250 = _aggregate_ee_image_to_training_grid(dem, target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    slope = ee.Terrain.slope(dem)
    slope_250 = _aggregate_ee_image_to_training_grid(slope, target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mean")
    dem_array = _sample_ee_image_to_2d(dem_250, target_roi, band="elevation").astype(np.float32)
    slope_array = _sample_ee_image_to_2d(slope_250, target_roi, band="slope").astype(np.float32)

    feature_stack = build_feature_stack(
        vv_t_arr,
        vh_t_arr,
        vv_t_1_arr,
        vh_t_1_arr,
        water_current=water_current.astype(np.float32),
        water_previous=water_previous.astype(np.float32),
        water_baseline=water_baseline.astype(np.float32),
        elevation=dem_array,
        slope=slope_array,
        fill_value=0.0,
    )

    feature_grid: dict[str, np.ndarray] = {}
    for name, value in feature_stack.items():
        if value is None or np.asarray(value).ndim != 2:
            continue
        feature_grid[name] = np.asarray(value, dtype=np.float32)

    gfd_reference = (
        ee.ImageCollection("GLOBAL_FLOOD_DB/MODIS_EVENTS/V1")
        .filterDate(gfd_start_date, gfd_end_date)
        .filterBounds(roi)
        .first()
    )
    if gfd_reference is None:
        raise ValueError("No GFD historical reference was found in the study area for the requested period.")

    flood_image = ee.Image(gfd_reference).select("flooded")
    permanent_water_image = ee.Image(gfd_reference).select("jrc_perm_water")
    future_reference = flood_image.eq(1).And(permanent_water_image.eq(0)).rename("flood_label")
    future_reference_250 = _aggregate_ee_image_to_training_grid(future_reference, target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mode")
    label_arr = _sample_ee_image_to_2d(future_reference_250, target_roi, band="flood_label", default_value=0.0).astype(np.bool_)
    permanent_water_250 = _aggregate_ee_image_to_training_grid(permanent_water_image, target_roi, crs=grid.crs, scale_m=grid.scale_m, reducer="mode")
    permanent_water_arr = _sample_ee_image_to_2d(permanent_water_250, target_roi, band="jrc_perm_water", default_value=0.0).astype(np.float32)
    permanent_water_excluded = int(np.count_nonzero(permanent_water_arr == 1.0))

    feature_grid, label_arr = _ensure_matching_grid(feature_grid, label_arr)
    for name, array in feature_grid.items():
        if array.shape != label_arr.shape:
            raise ValueError(f"Feature '{name}' shape {array.shape} does not match label shape {label_arr.shape}.")

    if target_dt != obs_dt + timedelta(days=DEFAULT_PREDICTION_HORIZON_DAYS):
        raise ValueError("Target timestamp is not exactly 7 days after the observation timestamp.")

    nan_count = 0
    inf_count = 0
    ranges: dict[str, tuple[float, float]] = {}
    for key, array in feature_grid.items():
        arr = np.asarray(array, dtype=np.float32)
        nan_count += int(np.count_nonzero(~np.isfinite(arr)))
        inf_count += int(np.count_nonzero(np.isinf(arr)))
        ranges[key] = (float(np.nanmin(arr)), float(np.nanmax(arr))) if arr.size else (0.0, 0.0)

    flood_reference_cells = int(np.count_nonzero(label_arr))
    valid_cells = int(label_arr.size)
    percentage = (flood_reference_cells / valid_cells * 100.0) if valid_cells else 0.0
    label_unique_values = tuple(sorted({int(v) for v in np.unique(label_arr).tolist()}))

    ordered_scene_ids = [str(item["id"]) for item in selected_unique]
    ordered_scene_timestamps = [datetime.fromtimestamp(int(ts) / 1000.0).isoformat() for ts in scene_timestamps]
    t_scene_id = ordered_scene_ids[-1] if ordered_scene_ids else None
    t_minus_1_scene_id = ordered_scene_ids[-2] if len(ordered_scene_ids) >= 2 else None
    t_minus_2_scene_id = ordered_scene_ids[-3] if len(ordered_scene_ids) >= 3 else None

    diagnostics = SamplingDiagnostics(
        selected_scene_ids=tuple(ordered_scene_ids),
        selected_scene_timestamps=tuple(ordered_scene_timestamps),
        t_scene_id=t_scene_id,
        t_minus_1_scene_id=t_minus_1_scene_id,
        t_minus_2_scene_id=t_minus_2_scene_id,
        observation_timestamp=obs_dt.isoformat(),
        target_timestamp=target_dt.isoformat(),
        crs=grid.crs,
        feature_grid_scale_m=float(grid.feature_scale_m),
        label_grid_scale_m=float(grid.scale_m),
        feature_dimensions=feature_grid["vv_t"].shape,
        label_dimensions=label_arr.shape,
        valid_cells=valid_cells,
        flood_reference_cells=flood_reference_cells,
        flood_reference_percentage=percentage,
        permanent_water_excluded=permanent_water_excluded,
        nan_count=nan_count,
        inf_count=inf_count,
        feature_ranges=ranges,
        label_unique_values=label_unique_values,
        spatial_alignment_confirmed=bool(feature_grid["vv_t"].shape == label_arr.shape and np.asarray(feature_grid["vv_t"]).shape == np.asarray(label_arr).shape),
    )

    return feature_grid, label_arr, {
        "diagnostics": diagnostics,
        "target_timestamp": target_dt,
        "selection_ids": scene_ids,
        "selection_timestamps": scene_timestamps,
        "grid": grid,
        "feature_grid_crs": grid.crs,
        "label_grid_crs": grid.crs,
        "feature_grid_scale_m": grid.feature_scale_m,
        "label_grid_scale_m": grid.scale_m,
    }


__all__ = [
    "DEFAULT_OBSERVATION_WINDOW_DAYS",
    "DEFAULT_PREDICTION_HORIZON_DAYS",
    "DEFAULT_TRAINING_GRID_CRS",
    "DEFAULT_TRAINING_GRID_SCALE_M",
    "GridSpec",
    "SamplingDiagnostics",
    "aggregate_feature_to_label_grid",
    "build_real_training_sample",
    "select_temporal_observation_scenes",
]
