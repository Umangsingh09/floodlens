from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from ai.config import AISettings, get_settings


def normalize_polarizations(value: str | Iterable[str] | None) -> list[str]:
    """Normalize a Sentinel-1 polarization specification to a stable list."""
    if value is None:
        return ["VV", "VH"]
    if isinstance(value, str):
        items = [p.strip() for p in value.replace(";", ",").split(",")]
    else:
        items = [str(p).strip() for p in value]
    normalized = [p.upper() for p in items if p]
    unique: list[str] = []
    seen: set[str] = set()
    for preferred in ["VV", "VH", "HH", "HV"]:
        if preferred in normalized and preferred not in seen:
            unique.append(preferred)
            seen.add(preferred)
    for item in normalized:
        if item and item not in seen:
            unique.append(item)
            seen.add(item)
    return unique or ["VV", "VH"]


def get_reference_projection(*, crs: str = "EPSG:32645", scale: float = 10.0) -> Any:
    """Return an explicit Earth Engine projection used to co-register Sentinel-1 scenes.

    The FloodLens AOI sits in the Bihar + southern Nepal corridor, which is within UTM zone
    45N. An explicit reference projection avoids false differences caused by per-scene native
    coordinate systems and orbit-specific geom footprints.
    """
    import ee  # type: ignore

    return ee.Projection(crs).atScale(scale)


def align_image_to_reference_grid(
    image: Any,
    roi: Any,
    *,
    crs: str = "EPSG:32645",
    scale: float = 10.0,
    resampling_method: str = "bilinear",
) -> Any:
    """Reproject and resample a Sentinel-1 image to one deterministic reference grid.

    Real Sentinel-1 scenes from different granules often have different native footprints and
    projection metadata even when they cover the same AOI. Projecting both scenes to a shared
    UTM grid and sampling the same ROI yields a common comparison grid required for temporal
    feature generation.
    """
    import ee  # type: ignore

    image_obj = ee.Image(image)
    roi_geom = ee.Geometry(roi)
    ref_projection = ee.Projection(crs).atScale(scale)
    roi_in_reference_crs = roi_geom.transform(crs, maxError=1)
    return image_obj.resample(resampling_method).reproject(ref_projection).clip(roi_in_reference_crs)


def _load_aoi(settings: AISettings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        return json.loads(settings.aoi_geojson)
    except json.JSONDecodeError as exc:  # pragma: no cover - guard against malformed config
        raise ValueError(f"AOI_GEOJSON is not valid JSON for region '{settings.region_name}'.") from exc


def _format_datetime(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value) / 1000.0, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str):
        raw = value.strip()
        if raw.endswith("Z"):
            return raw
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        except ValueError:
            return raw
    return str(value)


def summarize_discovery_result(raw_result: Mapping[str, Any]) -> dict[str, Any]:
    """Return a stable, JSON-friendly discovery summary."""
    total_scenes = int(raw_result.get("total_scenes", raw_result.get("scene_count", 0)))
    acquisition_dates = raw_result.get("acquisition_dates") or []
    dates: list[str] = []
    for value in acquisition_dates:
        timestamp = _format_datetime(value)
        if timestamp is None:
            continue
        dates.append(timestamp.split("T")[0])

    polarizations = normalize_polarizations(raw_result.get("polarizations") or raw_result.get("available_polarizations") or [])
    instrument_modes = raw_result.get("instrument_modes") or []
    orbit_passes = raw_result.get("orbit_passes") or []
    coverage = raw_result.get("coverage") or raw_result.get("spatial_coverage")
    resolution_meters = raw_result.get("resolution_meters")
    scene_details = raw_result.get("scene_details") or []

    return {
        "scene_count": total_scenes,
        "dates": dates,
        "polarizations": polarizations,
        "instrument_modes": list(instrument_modes),
        "orbit_passes": list(orbit_passes),
        "coverage": coverage,
        "resolution_meters": resolution_meters,
        "region_name": raw_result.get("region_name"),
        "collection": raw_result.get("collection"),
        "provider": raw_result.get("provider"),
        "scene_details": scene_details,
    }


def _format_earth_engine_instructions() -> str:
    return "\n".join(
        [
            "Earth Engine authentication is required before Sentinel-1 discovery can run.",
            "",
            "1. Install the dependency:",
            "   python -m pip install earthengine-api",
            "2. Authenticate with Google Earth Engine:",
            "   earthengine authenticate",
            "3. If using a GEE project, set the environment variable:",
            "   set EARTH_ENGINE_PROJECT=your-project-id",
            "   (or export EARTH_ENGINE_PROJECT=your-project-id on Unix shells)",
            "4. Re-run:",
            "   python -m ai.preprocessing.sentinel1 --discover",
        ]
    )


def fail_with_auth_instructions(message: str) -> int:
    print(message, file=sys.stderr)
    print("", file=sys.stderr)
    print(_format_earth_engine_instructions(), file=sys.stderr)
    return 2


def discover_sentinel1_scenes(settings: AISettings | None = None) -> dict[str, Any]:
    """Discover Sentinel-1 GRD scenes for the Bihar + southern Nepal flood corridor.

    This is discovery-only; it does not download the full dataset. It reports the
    matching scene count, dates, available polarizations, instrument mode,
    orbit metadata, spatial coverage, and resolution information for each scene.
    """
    settings = settings or get_settings()

    try:
        import ee  # type: ignore
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Earth Engine Python API is not installed. Run: python -m pip install earthengine-api"
        ) from exc

    try:
        if settings.earthengine_project:
            ee.Initialize(project=settings.earthengine_project)
        else:
            ee.Initialize()
    except Exception as exc:  # pragma: no cover - depends on runtime auth state
        raise RuntimeError(f"Earth Engine is not initialized/authenticated: {exc}") from exc

    aoi = _load_aoi(settings)
    geometry = ee.Geometry(aoi)

    collection = ee.ImageCollection(settings.satellite_collection)
    collection = collection.filterBounds(geometry)
    collection = collection.filterDate(settings.start_date, settings.end_date)
    collection = collection.filter(ee.Filter.eq("instrumentMode", settings.instrument_mode))

    required_pols = normalize_polarizations(settings.polarizations)
    for pol in required_pols:
        collection = collection.filter(ee.Filter.listContains("transmitterReceiverPolarisation", pol))

    total_scenes = int(collection.size().getInfo())
    sample = collection.sort("system:time_start", False).limit(25).getInfo()

    acquisition_dates: list[str] = []
    polarizations: set[str] = set()
    instrument_modes: set[str] = set()
    orbit_passes: set[str] = set()
    scene_details: list[dict[str, Any]] = []

    for scene in sample.get("features", []):
        props = scene.get("properties", {})
        scene_id = props.get("system:index") or props.get("sceneID") or props.get("product_id")
        timestamp = props.get("system:time_start")
        iso_dt = _format_datetime(timestamp) if timestamp is not None else None
        if iso_dt is not None:
            acquisition_dates.append(iso_dt)
        for value in props.get("transmitterReceiverPolarisation", []) or []:
            polarizations.add(str(value).upper())
        mode = props.get("instrumentMode")
        if mode:
            instrument_modes.add(str(mode).upper())
        orbit_pass = props.get("orbitProperties_pass") or props.get("orbit_pass")
        if orbit_pass:
            orbit_passes.add(str(orbit_pass).upper())

        scene_details.append(
            {
                "scene_id": scene_id,
                "acquisition_date": iso_dt,
                "orbit_pass": str(orbit_pass).upper() if orbit_pass else None,
                "instrument_mode": str(mode).upper() if mode else settings.instrument_mode.upper(),
                "polarizations": sorted({str(v).upper() for v in (props.get("transmitterReceiverPolarisation", []) or [])}),
                "resolution_meters": props.get("resolution_meters"),
            }
        )

    if total_scenes > 0:
        first_image = ee.Image(collection.sort("system:time_start").first())
        resolution = float(first_image.select(0).projection().nominalScale().getInfo())
        coverage = collection.geometry().bounds().getInfo()
    else:
        resolution = None
        coverage = aoi

    return {
        "provider": settings.satellite_provider,
        "collection": settings.satellite_collection,
        "region_name": settings.region_name,
        "aoi_name": settings.aoi_name,
        "start_date": settings.start_date,
        "end_date": settings.end_date,
        "instrument_mode": settings.instrument_mode,
        "polarizations": sorted(polarizations or set(required_pols)),
        "total_scenes": total_scenes,
        "acquisition_dates": acquisition_dates,
        "instrument_modes": sorted(instrument_modes or [settings.instrument_mode.upper()]),
        "orbit_passes": sorted(orbit_passes),
        "coverage": coverage,
        "resolution_meters": resolution,
        "spatial_coverage": coverage,
        "available_polarizations": sorted(polarizations or set(required_pols)),
        "scene_details": scene_details,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FloodLens Sentinel-1 discovery pipeline")
    parser.add_argument("--discover", action="store_true", help="Discover matching Sentinel-1 GRD scenes for the configured AOI and date range.")
    parser.add_argument("--export", action="store_true", help="Reserved for future export/download work; Phase 1 discovery only.")
    parser.add_argument("--start-date", default=None, help="Override the configured start date for discovery.")
    parser.add_argument("--end-date", default=None, help="Override the configured end date for discovery.")
    parser.add_argument("--project-id", default=None, help="Override the configured Google Earth Engine project ID.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.export and not args.discover:
        print("Export/download mode is not implemented in Phase 1; discovery is the supported operation.", file=sys.stderr)
        return 1

    if not args.discover:
        parser.print_help()
        return 1

    settings = get_settings()
    if args.start_date:
        settings = AISettings(**{**settings.__dict__, "start_date": args.start_date})
    if args.end_date:
        settings = AISettings(**{**settings.__dict__, "end_date": args.end_date})
    if args.project_id:
        settings = AISettings(**{**settings.__dict__, "earthengine_project": args.project_id})

    try:
        discovery = discover_sentinel1_scenes(settings)
    except RuntimeError as exc:
        return fail_with_auth_instructions(str(exc))
    except Exception as exc:  # pragma: no cover - runtime GEE or config failures
        return fail_with_auth_instructions(f"Discovery failed: {exc}")

    print(json.dumps(summarize_discovery_result(discovery), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
