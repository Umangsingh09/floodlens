from __future__ import annotations

import numpy as np

from ai.preprocessing.dem_features import compute_dem_features


def _as_2d_array(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=np.float32)
    if array.ndim == 0:
        return array.reshape(1, 1)
    if array.ndim == 1:
        return array.reshape(1, -1)
    return array


def _align_to_common_shape(*arrays: np.ndarray) -> list[np.ndarray]:
    valid = [np.asarray(array, dtype=np.float32) for array in arrays if array is not None]
    if not valid:
        return []

    max_rows = max(int(array.shape[0]) for array in valid)
    max_cols = max(int(array.shape[1]) for array in valid)
    aligned: list[np.ndarray] = []
    for array in valid:
        if array.shape == (max_rows, max_cols):
            aligned.append(array)
            continue
        padded = np.zeros((max_rows, max_cols), dtype=np.float32)
        rows = min(array.shape[0], max_rows)
        cols = min(array.shape[1], max_cols)
        padded[:rows, :cols] = array[:rows, :cols]
        aligned.append(padded)
    return aligned


def compute_temporal_change(current: np.ndarray, previous: np.ndarray) -> np.ndarray:
    """Compute the difference between current and previous observations."""
    current_arr = _as_2d_array(np.nan_to_num(current, nan=0.0, posinf=0.0, neginf=0.0))
    previous_arr = _as_2d_array(np.nan_to_num(previous, nan=0.0, posinf=0.0, neginf=0.0))
    if current_arr.shape != previous_arr.shape:
        raise ValueError("Current and previous arrays must have matching dimensions.")
    return current_arr - previous_arr


def compute_water_trend(current: np.ndarray, previous: np.ndarray) -> np.ndarray:
    """Compute a simple temporal water trend from the current and previous water state."""
    current_arr = np.asarray(current, dtype=np.float32)
    previous_arr = np.asarray(previous, dtype=np.float32)
    if current_arr.shape != previous_arr.shape:
        raise ValueError("Current and previous water arrays must have matching dimensions.")
    return current_arr - previous_arr


def build_temporal_water_features(
    water_current: np.ndarray,
    water_previous: np.ndarray,
    water_baseline: np.ndarray,
    *,
    timestamps: np.ndarray | None = None,
    fill_value: float = 0.0,
) -> dict[str, np.ndarray]:
    """Build water persistence, change, and trend features for Sentinel-1 time series."""
    current_arr = _as_2d_array(np.nan_to_num(water_current, nan=fill_value, posinf=fill_value, neginf=fill_value))
    previous_arr = _as_2d_array(np.nan_to_num(water_previous, nan=fill_value, posinf=fill_value, neginf=fill_value))
    baseline_arr = _as_2d_array(np.nan_to_num(water_baseline, nan=fill_value, posinf=fill_value, neginf=fill_value))

    if current_arr.shape != previous_arr.shape or current_arr.shape != baseline_arr.shape:
        raise ValueError("Water arrays must share the same spatial dimensions.")

    water_change = current_arr - previous_arr
    water_persistence = current_arr + previous_arr
    trend = current_arr - baseline_arr
    if timestamps is not None and len(np.asarray(timestamps)) > 0:
        trend = trend.astype(np.float32)

    features = {
        "water_current": current_arr,
        "water_previous": previous_arr,
        "water_change": water_change,
        "water_persistence": water_persistence,
        "water_baseline": baseline_arr,
        "water_trend": trend,
    }
    return features


def build_feature_stack(
    vv_t: np.ndarray,
    vh_t: np.ndarray,
    vv_t_1: np.ndarray,
    vh_t_1: np.ndarray,
    *,
    fill_value: float = 0.0,
    water_current: np.ndarray | None = None,
    water_previous: np.ndarray | None = None,
    water_baseline: np.ndarray | None = None,
    elevation: np.ndarray | None = None,
    slope: np.ndarray | None = None,
    rainfall_7d: np.ndarray | None = None,
    soil_moisture: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Build interpretable Sentinel-1 temporal features.

    The feature names are explicit so a later model can consume a clear,
    reproducible stack: VV/VH at the current and previous timestamps, changes,
    and water-derived temporal indicators.
    """
    vv_t_arr = _as_2d_array(np.nan_to_num(vv_t, nan=fill_value, posinf=fill_value, neginf=fill_value))
    vh_t_arr = _as_2d_array(np.nan_to_num(vh_t, nan=fill_value, posinf=fill_value, neginf=fill_value))
    vv_prev_arr = _as_2d_array(np.nan_to_num(vv_t_1, nan=fill_value, posinf=fill_value, neginf=fill_value))
    vh_prev_arr = _as_2d_array(np.nan_to_num(vh_t_1, nan=fill_value, posinf=fill_value, neginf=fill_value))

    vv_t_arr, vh_t_arr, vv_prev_arr, vh_prev_arr = _align_to_common_shape(vv_t_arr, vh_t_arr, vv_prev_arr, vh_prev_arr)

    if vv_t_arr.shape != vv_prev_arr.shape or vh_t_arr.shape != vh_prev_arr.shape:
        raise ValueError("Feature arrays must have matching spatial dimensions.")

    features = {
        "vv_t": vv_t_arr,
        "vh_t": vh_t_arr,
        "vv_t_1": vv_prev_arr,
        "vh_t_1": vh_prev_arr,
        "delta_vv": vv_t_arr - vv_prev_arr,
        "delta_vh": vh_t_arr - vh_prev_arr,
    }

    if water_current is not None:
        features["water_current"] = _as_2d_array(np.nan_to_num(water_current, nan=fill_value, posinf=fill_value, neginf=fill_value))
    if water_previous is not None:
        features["water_previous"] = _as_2d_array(np.nan_to_num(water_previous, nan=fill_value, posinf=fill_value, neginf=fill_value))
    if water_baseline is not None:
        features["water_baseline"] = _as_2d_array(np.nan_to_num(water_baseline, nan=fill_value, posinf=fill_value, neginf=fill_value))

    if water_current is not None and water_previous is not None:
        water_current_arr, water_previous_arr = _align_to_common_shape(features["water_current"], features["water_previous"])
        features["water_current"] = water_current_arr
        features["water_previous"] = water_previous_arr
        features["water_change"] = features["water_current"] - features["water_previous"]
    if water_current is not None and water_baseline is not None:
        water_current_arr, water_baseline_arr = _align_to_common_shape(features["water_current"], features["water_baseline"])
        features["water_current"] = water_current_arr
        features["water_baseline"] = water_baseline_arr
        features["water_trend"] = features["water_current"] - features["water_baseline"]
    if water_current is not None and water_previous is not None:
        features["water_persistence"] = features["water_current"] + features["water_previous"]

    if elevation is not None or slope is not None:
        elevation_arr = _as_2d_array(np.nan_to_num(elevation if elevation is not None else np.zeros_like(vv_t_arr, dtype=np.float32), nan=fill_value, posinf=fill_value, neginf=fill_value))
        slope_arr = _as_2d_array(np.nan_to_num(slope if slope is not None else np.zeros_like(vv_t_arr, dtype=np.float32), nan=fill_value, posinf=fill_value, neginf=fill_value))
        elevation_arr, slope_arr = _align_to_common_shape(elevation_arr, slope_arr)
        if elevation_arr.shape != slope_arr.shape:
            raise ValueError("Elevation and slope arrays must have matching dimensions.")
        features.update({"elevation": elevation_arr, "slope": slope_arr})

    if rainfall_7d is not None:
        features["rainfall_7d"] = _as_2d_array(
            np.nan_to_num(rainfall_7d, nan=fill_value, posinf=fill_value, neginf=fill_value)
        )

    if soil_moisture is not None:
        features["soil_moisture"] = _as_2d_array(
            np.nan_to_num(soil_moisture, nan=fill_value, posinf=fill_value, neginf=fill_value)
        )

    return features
