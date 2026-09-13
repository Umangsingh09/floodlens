"""Real-time flood-risk inference.

Fetches the most recent real Sentinel-1 observation window (rolling lookback ending "now"),
builds the same feature grid used in training, and runs the trained model on it. No label is
used or available here — there is no future ground truth for the present moment. Writes the
prediction contract the backend expects into `ai/outputs/<prediction_id>/`.

`run_prediction()` is the reusable entry point (used by the backend's refresh endpoint and its
startup scheduler); running this file directly does the same thing from the command line:
    PYTHONPATH=. python -m ai.inference.predict_current_risk
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ee
import numpy as np
import rasterio
from rasterio.transform import from_bounds

from ai.config import get_settings
from ai.earthengine_auth import initialize_earth_engine
from ai.models.risk_model import LogisticRiskModel
from ai.preprocessing.real_gee_sampling import GridSpec, build_live_feature_grid

logger = logging.getLogger(__name__)

# Same real, Sentinel-1-covered sample region used for training, inside the Bihar-Nepal AOI.
LIVE_SAMPLE_REGION_BBOX = (85.715, 26.13, 85.865, 26.27)
MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "artifacts" / "flood_risk_logreg.joblib"
OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "outputs"
PREDICTION_HORIZON_HOURS = 24 * 7


def _flatten_feature_grid(feature_grid: dict[str, np.ndarray], feature_names: list[str]) -> np.ndarray:
    columns = [np.asarray(feature_grid[name], dtype=np.float32).reshape(-1) for name in feature_names]
    return np.stack(columns, axis=1)


def run_prediction(*, output_root: Path | None = None) -> dict[str, Any]:
    """Run one real live inference pass and write its outputs. Returns the metadata dict."""
    output_root = output_root or OUTPUT_ROOT

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"No trained model found at {MODEL_PATH}. Run `python -m ai.training.train_risk_model` first."
        )

    settings = get_settings()
    logger.info("Starting live risk prediction (project=%s)", settings.earthengine_project)
    initialize_earth_engine(project=settings.earthengine_project)

    model = LogisticRiskModel.load(str(MODEL_PATH))
    if not model.feature_names:
        raise ValueError("Loaded model has no recorded feature_names; cannot align live features to it.")

    sample_region = ee.Geometry.BBox(*LIVE_SAMPLE_REGION_BBOX)
    now_utc = datetime.now(timezone.utc)

    feature_grid, meta = build_live_feature_grid(
        json.loads(settings.aoi_geojson),
        now_utc.replace(tzinfo=None),
        settings=settings,
        sample_region=sample_region,
        grid_spec=GridSpec(),
        min_scene_count=3,
        max_lookback_days=45,
    )

    grid_shape = feature_grid[model.feature_names[0]].shape
    X = _flatten_feature_grid(feature_grid, model.feature_names)
    risk = model.predict_proba(X)[:, 1].reshape(grid_shape).astype(np.float32)

    risk_summary = {
        "min": float(np.nanmin(risk)),
        "max": float(np.nanmax(risk)),
        "mean": float(np.nanmean(risk)),
    }

    prediction_id = now_utc.strftime("%Y%m%dT%H%M%SZ")
    prediction_dir = output_root / prediction_id
    prediction_dir.mkdir(parents=True, exist_ok=True)

    minx, miny, maxx, maxy = LIVE_SAMPLE_REGION_BBOX
    transform = from_bounds(minx, miny, maxx, maxy, grid_shape[1], grid_shape[0])
    raster_path = prediction_dir / "risk_raster.tif"
    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=grid_shape[0],
        width=grid_shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(risk, 1)

    processing_lag_seconds = meta.get("processing_lag_seconds")
    metadata = {
        "regionId": settings.region_name,
        "hazard": "flood",
        "risk": risk_summary,
        "resolutionMeters": float(GridSpec().scale_m),
        "crs": "EPSG:4326",
        "bounds": {"west": minx, "south": miny, "east": maxx, "north": maxy},
        "satellite": "Sentinel-1",
        "sourcePassTimestamp": meta.get("latest_scene_timestamp"),
        "predictionTimestamp": meta.get("prediction_timestamp"),
        "processingLagSeconds": processing_lag_seconds if processing_lag_seconds is not None else 0,
        "predictionHorizonHours": PREDICTION_HORIZON_HOURS,
        "modelId": "logistic-regression",
        "modelVersion": "0.1.0-baseline",
        "alert": {"threshold": settings.risk_threshold},
        "observationWindowScenes": meta.get("selected_scene_ids"),
        "gridShape": list(grid_shape),
        "note": "Baseline model trained on a single real 2017 historical event; treat as a hackathon proof of pipeline, not a calibrated production forecast.",
    }
    (prediction_dir / "prediction_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    logger.info(
        "Prediction '%s' written: mean_risk=%.3f lag_seconds=%s",
        prediction_id,
        risk_summary["mean"],
        processing_lag_seconds,
    )

    return {"predictionId": prediction_id, "predictionDir": str(prediction_dir), **metadata}


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    metadata = run_prediction()
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
