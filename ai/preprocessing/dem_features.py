from __future__ import annotations

import numpy as np


def compute_dem_features(elevation: np.ndarray, slope: np.ndarray, *, fill_value: float = 0.0) -> dict[str, np.ndarray]:
    """Return aligned elevation and slope raster arrays.

    This supports configurable DEM products that may need to be aligned to the
    Sentinel-1 analysis grid. The arrays are converted to floating point and
    invalid values are replaced with a fill value to keep feature stacks stable.
    """
    elevation_arr = np.asarray(elevation, dtype=np.float32)
    slope_arr = np.asarray(slope, dtype=np.float32)

    if elevation_arr.shape != slope_arr.shape:
        raise ValueError("Elevation and slope arrays must have matching dimensions.")

    elevation_arr = np.nan_to_num(elevation_arr, nan=fill_value, posinf=fill_value, neginf=fill_value)
    slope_arr = np.nan_to_num(slope_arr, nan=fill_value, posinf=fill_value, neginf=fill_value)

    return {
        "elevation": elevation_arr,
        "slope": slope_arr,
    }
