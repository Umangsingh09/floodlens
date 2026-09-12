from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import numpy as np

GFD_DATASET = "GLOBAL_FLOOD_DB/MODIS_EVENTS/V1"
GFD_VALIDATION_DFO_ID = 4507
GFD_VALIDATION_START = "2017-08-10"
GFD_VALIDATION_END = "2017-08-26"
GFD_VALIDATION_END_EXCLUSIVE = "2017-08-27"
GFD_REFERENCE_TYPE = "remotely sensed historical reference"
GFD_REFERENCE_RESOLUTION_M = 250.0
GFD_REFERENCE_CRS = "EPSG:4326"


@dataclass(frozen=True)
class GFDReferenceSummary:
    """Container for the validated GFD historical event metadata."""

    dfo_id: int
    image_id: str
    start_date: str
    end_date: str
    primary_country: str
    countries: str
    resolution_m: float = GFD_REFERENCE_RESOLUTION_M
    reference_type: str = GFD_REFERENCE_TYPE


def build_gfd_flood_reference(
    flooded: np.ndarray,
    permanent_water: np.ndarray,
    *,
    nodata: float | None = None,
    flood_value: float = 1.0,
    permanent_water_value: float = 0.0,
) -> np.ndarray:
    """Return the historical flood reference mask.

    The reference definition is explicit and non-negotiable:
    flooded == 1 AND jrc_perm_water == 0.
    """
    flooded_array = np.asarray(flooded, dtype=np.float32)
    permanent_array = np.asarray(permanent_water, dtype=np.float32)

    if flooded_array.shape != permanent_array.shape:
        raise ValueError("flooded and permanent_water must have identical shapes")

    valid = np.ones_like(flooded_array, dtype=bool)
    if nodata is not None:
        valid &= np.isfinite(flooded_array) & np.isfinite(permanent_array)
        valid &= flooded_array != nodata
        valid &= permanent_array != nodata

    reference = np.zeros_like(flooded_array, dtype=bool)
    reference[valid] = (flooded_array[valid] == flood_value) & (permanent_array[valid] == permanent_water_value)
    return reference


def compute_reference_area_m2(reference_mask: np.ndarray, *, pixel_size_m: float = GFD_REFERENCE_RESOLUTION_M) -> float:
    """Compute inundated area in square meters using the GFD pixel size."""
    mask = np.asarray(reference_mask, dtype=bool)
    valid_pixels = int(np.count_nonzero(mask))
    return float(valid_pixels * (pixel_size_m * pixel_size_m))


def compute_reference_coverage(
    aoi_mask: np.ndarray,
    flood_reference: np.ndarray,
    *,
    pixel_size_m: float = GFD_REFERENCE_RESOLUTION_M,
) -> tuple[float, float, int, int]:
    """Return area, coverage percentage, valid pixels, and flood pixels."""
    aoi_array = np.asarray(aoi_mask, dtype=bool)
    ref_array = np.asarray(flood_reference, dtype=bool)
    if aoi_array.shape != ref_array.shape:
        raise ValueError("aoi_mask and flood_reference must have identical shapes")

    aoi_pixels = int(np.count_nonzero(aoi_array))
    flood_pixels = int(np.count_nonzero(ref_array))
    aoi_area_m2 = float(aoi_pixels * (pixel_size_m * pixel_size_m))
    flood_area_m2 = float(flood_pixels * (pixel_size_m * pixel_size_m))
    coverage_pct = (flood_area_m2 / aoi_area_m2 * 100.0) if aoi_area_m2 > 0 else 0.0
    return flood_area_m2, coverage_pct, aoi_pixels, flood_pixels


def select_gfd_event(events: Iterable[Mapping[str, Any]], dfo_id: int = GFD_VALIDATION_DFO_ID) -> Mapping[str, Any]:
    """Select the requested DFO flood event from a collection of event metadata."""
    for event in events:
        if int(event.get("id", -1)) == int(dfo_id):
            return event
    raise ValueError(f"No event found for DFO ID={dfo_id}")


def create_gfd_validation_event_metadata() -> GFDReferenceSummary:
    """Return the validated DFO 4507 metadata for the historical reference run."""
    return GFDReferenceSummary(
        dfo_id=GFD_VALIDATION_DFO_ID,
        image_id="DFO_4507_From_20170810_to_20170826",
        start_date=GFD_VALIDATION_START,
        end_date=GFD_VALIDATION_END,
        primary_country="India",
        countries="China, India, Pakistan, Nepal, Bangladesh",
        resolution_m=GFD_REFERENCE_RESOLUTION_M,
        reference_type=GFD_REFERENCE_TYPE,
    )


def get_earthengine_gfd_collection() -> Any:
    """Return the Earth Engine image collection object for the GFD historical dataset."""
    import ee

    return ee.ImageCollection(GFD_DATASET)


def get_dfo_4507_reference_image(aoi_geometry: Any, *, start_date: str = GFD_VALIDATION_START, end_date: str = GFD_VALIDATION_END_EXCLUSIVE) -> Any:
    """Return the DFO 4507 flood reference clipped to the study AOI.

    This function intentionally uses the explicit rule:
        flooded == 1 AND jrc_perm_water == 0
    """
    import ee

    collection = get_earthengine_gfd_collection()
    event = (
        collection.filter(ee.Filter.eq("id", GFD_VALIDATION_DFO_ID))
        .filterDate(start_date, end_date)
        .filterBounds(aoi_geometry)
        .first()
    )
    if event is None:
        raise ValueError(f"No GFD event found for DFO {GFD_VALIDATION_DFO_ID} in the AOI and date window")

    flooded = ee.Image(event).select("flooded")
    permanent_water = ee.Image(event).select("jrc_perm_water")
    reference = flooded.eq(1).And(permanent_water.eq(0))
    return reference.clip(aoi_geometry)


def build_gfd_reference_export_task(
    aoi_geometry: Any,
    *,
    description: str = "floodlens_gfd_dfo_4507_reference",
    scale: float = GFD_REFERENCE_RESOLUTION_M,
    crs: str = GFD_REFERENCE_CRS,
    file_format: str = "GeoTIFF",
    bucket: str | None = None,
    folder: str = "floodlens",
) -> Any:
    """Prepare an Earth Engine export task for the validated DFO 4507 reference."""
    import ee

    image = get_dfo_4507_reference_image(aoi_geometry)
    export_args = {
        "image": image,
        "description": description,
        "region": aoi_geometry,
        "scale": scale,
        "crs": crs,
        "fileFormat": file_format,
    }
    if bucket is not None:
        export_args["bucket"] = bucket
        export_args["folder"] = folder
    return ee.batch.Export.image.toCloudStorage(**export_args) if bucket is not None else ee.batch.Export.image.toDrive(**export_args)


__all__ = [
    "GFD_DATASET",
    "GFD_REFERENCE_CRS",
    "GFD_REFERENCE_RESOLUTION_M",
    "GFD_REFERENCE_TYPE",
    "GFD_VALIDATION_DFO_ID",
    "GFD_VALIDATION_END",
    "GFD_VALIDATION_END_EXCLUSIVE",
    "GFD_VALIDATION_START",
    "GFDReferenceSummary",
    "build_gfd_flood_reference",
    "build_gfd_reference_export_task",
    "compute_reference_area_m2",
    "compute_reference_coverage",
    "create_gfd_validation_event_metadata",
    "get_dfo_4507_reference_image",
    "get_earthengine_gfd_collection",
    "select_gfd_event",
]
