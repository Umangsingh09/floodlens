"""Train the baseline flood-risk model on a real, labeled historical sample.

Training requires a KNOWN outcome (did it flood 7 days after the observation?), which only
exists for a real historical event — there is no future ground truth for "now". This script
pulls a real Sentinel-1 + GFD (DFO 4507, Aug 2017) sample via live Earth Engine calls, treats
every 250 m grid cell as one training row, and fits `LogisticRiskModel` on it.

Run from the repo root with the backend venv active:
    PYTHONPATH=. python -m ai.training.train_risk_model
"""

from __future__ import annotations

import json
from pathlib import Path

import ee
import numpy as np
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

from ai.config import get_settings
from ai.gee_auth import initialize_earth_engine
from ai.models.risk_model import LogisticRiskModel
from ai.preprocessing.real_gee_sampling import GridSpec, build_real_training_sample

# Real, historically validated flooded location within the Bihar-Nepal AOI for DFO 4507
# (see docs/AI_INTEGRATION.md for the historical reference). Chosen because it actually
# contains both flooded and non-flooded grid cells per the GFD reference.
TRAINING_SAMPLE_REGION_BBOX = (85.77, 26.18, 85.81, 26.22)
TRAINING_OBSERVATION_TIMESTAMP = "2017-08-21T00:00:00"

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "models" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "flood_risk_logreg.joblib"
REPORT_PATH = ARTIFACT_DIR / "training_report.json"
MODEL_VERSION = "0.1.0-baseline"


def _flatten_feature_grid(feature_grid: dict[str, np.ndarray]) -> tuple[np.ndarray, list[str]]:
    feature_names = sorted(feature_grid.keys())
    columns = [np.asarray(feature_grid[name], dtype=np.float32).reshape(-1) for name in feature_names]
    return np.stack(columns, axis=1), feature_names


def main() -> None:
    settings = get_settings()
    initialize_earth_engine(project=settings.earthengine_project)

    sample_region = ee.Geometry.BBox(*TRAINING_SAMPLE_REGION_BBOX)
    feature_grid, label_arr, extra = build_real_training_sample(
        json.loads(settings.aoi_geojson),
        TRAINING_OBSERVATION_TIMESTAMP,
        settings=settings,
        sample_region=sample_region,
        grid_spec=GridSpec(),
        min_scene_count=3,
        max_lookback_days=30,
    )

    X, feature_names = _flatten_feature_grid(feature_grid)
    y = np.asarray(label_arr, dtype=int).reshape(-1)

    if len(np.unique(y)) < 2:
        raise ValueError("Training sample has only one label class; cannot fit a classifier.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    eval_model = LogisticRiskModel().fit(X_train, y_train, feature_names=feature_names)
    test_proba = eval_model.predict_proba(X_test)[:, 1]
    test_auc = float(roc_auc_score(y_test, test_proba))
    test_accuracy = float((eval_model.predict(X_test) == y_test).mean())

    final_model = LogisticRiskModel().fit(X, y, feature_names=feature_names)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    final_model.save(str(MODEL_PATH))

    diagnostics = extra["diagnostics"]
    report = {
        "model_version": MODEL_VERSION,
        "model_type": "logistic_regression",
        "feature_names": feature_names,
        "training_rows": int(X.shape[0]),
        "positive_rows": int(y.sum()),
        "negative_rows": int((y == 0).sum()),
        "held_out_test_rows": int(X_test.shape[0]),
        "held_out_test_auc": test_auc,
        "held_out_test_accuracy": test_accuracy,
        "training_data_source": "real Sentinel-1 GRD + GFD DFO 4507 (Aug 2017), Bihar-Nepal AOI",
        "not_real_time": True,
        "observation_timestamp": diagnostics.observation_timestamp,
        "target_timestamp": diagnostics.target_timestamp,
        "selected_scene_ids": list(diagnostics.selected_scene_ids),
        "grid_crs": diagnostics.crs,
        "grid_scale_m": diagnostics.label_grid_scale_m,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
