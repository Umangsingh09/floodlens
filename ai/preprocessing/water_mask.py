from __future__ import annotations

import numpy as np


class WaterMaskArray(np.ndarray):
    """NumPy array subclass that exposes Python bool scalars for scalar access."""

    def __getitem__(self, key):
        result = super().__getitem__(key)
        if np.isscalar(result):
            return bool(result)
        return result


def compute_water_mask(
    backscatter: np.ndarray,
    threshold: float | None = None,
    nodata: float | None = None,
    *,
    invert: bool = False,
) -> np.ndarray:
    """Generate a binary water mask from Sentinel-1 backscatter in dB.

    A lower backscatter value generally indicates smoother, darker surfaces such as
    open water. The threshold is configurable so the hydrologic behavior can be tuned
    for different seasons or AOIs without hardcoding a magic number.
    """
    array = np.asarray(backscatter, dtype=np.float32)
    if threshold is None:
        threshold = -12.0

    valid = np.isfinite(array)
    if nodata is not None:
        valid &= array != nodata

    water = np.zeros_like(array, dtype=bool).view(WaterMaskArray)
    if valid.any():
        water[valid] = array[valid] <= threshold
    if invert:
        water = ~water
    return water
