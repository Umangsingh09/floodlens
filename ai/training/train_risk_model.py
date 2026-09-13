"""Train the baseline flood-risk model on real, labeled historical samples.

Training requires a KNOWN outcome (did it flood 7 days after the observation?), which only
exists for a real historical event — there is no future ground truth for "now". This script
pulls real Sentinel-1 + GFD samples for multiple real historical events via live Earth Engine
calls, treats every 250 m grid cell as one training row, and fits `LogisticRiskModel` on the
combined data.

Multiple events matter beyond just more rows: a feature like rainfall is constant within any
single historical snapshot (one date has one rainfall total), so a model trained on only one
event has zero variance to learn a real rainfall/soil-moisture relationship from — its
coefficient for that feature is essentially arbitrary (this caused a real production bug once;
see LogisticRiskModel's clipping safeguard). Events from different years/months give real
variation in those features to learn from instead.

Held-out evaluation trains on all-but-one event and tests entirely on the omitted one — a
stronger, more honest check than a random cell-level split within one event, which spatial
autocorrelation between neighboring cells could make look better than it really is. This
directly answers "does this generalize to conditions it never saw," not just "does it fit this
one event's cells."

Run from the repo root with the backend venv active:
    PYTHONPATH=. python -m ai.training.train_risk_model
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import ee
import numpy as np
from sklearn.metrics import roc_auc_score

from ai.config import get_settings
from ai.gee_auth import initialize_earth_engine
from ai.models.risk_model import MODEL_VERSION, LogisticRiskModel
from ai.preprocessing.real_gee_sampling import GridSpec, build_real_training_sample

# The same real, Sentinel-1-covered sample region used for live inference, inside the
# Bihar-Nepal AOI — ~3.8k 250m cells (~17km x 15km).
TRAINING_SAMPLE_REGION_BBOX = (85.715, 26.13, 85.865, 26.27)


@dataclass(frozen=True)
class TrainingEvent:
    name: str
    observation_timestamp: str
    gfd_start_date: str
    gfd_end_date: str


# Real historical flood events verified live against the actual GFD dataset at this exact
# sample region before being added here — both have real, non-degenerate flood-label variation
# (checked via reduceRegion) and real Sentinel-1 scenes available before their observation date.
# A third real GFD event at this bbox (id 4382, Jul-Aug 2016) was checked and rejected: no
# Sentinel-1 scenes with real signal were found in this ROI for that period (2016 predates
# reliable Sentinel-1 revisit coverage over this part of South Asia) — not fabricated, just
# genuinely unavailable, so it's left out rather than forced.
TRAINING_EVENTS = [
    TrainingEvent(
        name="dfo-4507-2017-08",
        observation_timestamp="2017-08-21T00:00:00",
        gfd_start_date="2017-08-10",
        gfd_end_date="2017-08-27",
    ),
    TrainingEvent(
        name="gfd-4673-2018-09",
        observation_timestamp="2018-09-03T00:00:00",
        gfd_start_date="2018-09-01",
        gfd_end_date="2018-09-09",
    ),
]

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "models" / "artifacts"
MODEL_PATH = ARTIFACT_DIR / "flood_risk_logreg.joblib"
REPORT_PATH = ARTIFACT_DIR / "training_report.json"


def _flatten_feature_grid(feature_grid: dict[str, np.ndarray]) -> tuple[np.ndarray, list[str]]:
    feature_names = sorted(feature_grid.keys())
    columns = [np.asarray(feature_grid[name], dtype=np.float32).reshape(-1) for name in feature_names]
    return np.stack(columns, axis=1), feature_names


def _build_event_sample(event: TrainingEvent, *, settings, sample_region, aoi) -> dict:
    feature_grid, label_arr, extra = build_real_training_sample(
        aoi,
        event.observation_timestamp,
        settings=settings,
        sample_region=sample_region,
        grid_spec=GridSpec(),
        min_scene_count=3,
        max_lookback_days=30,
        gfd_start_date=event.gfd_start_date,
        gfd_end_date=event.gfd_end_date,
    )
    X, feature_names = _flatten_feature_grid(feature_grid)
    y = np.asarray(label_arr, dtype=int).reshape(-1)
    if len(np.unique(y)) < 2:
        raise ValueError(f"Event '{event.name}' has only one label class; cannot use it for training.")
    return {
        "event": event,
        "X": X,
        "y": y,
        "feature_names": feature_names,
        "diagnostics": extra["diagnostics"],
    }


def main() -> None:
    settings = get_settings()
    initialize_earth_engine(project=settings.earthengine_project)

    aoi = json.loads(settings.aoi_geojson)
    sample_region = ee.Geometry.BBox(*TRAINING_SAMPLE_REGION_BBOX)

    samples = [_build_event_sample(event, settings=settings, sample_region=sample_region, aoi=aoi) for event in TRAINING_EVENTS]

    feature_names = samples[0]["feature_names"]
    for sample in samples[1:]:
        if sample["feature_names"] != feature_names:
            raise ValueError(
                f"Feature set mismatch between events: {samples[0]['event'].name} has "
                f"{feature_names} but {sample['event'].name} has {sample['feature_names']}."
            )

    # Held-out evaluation: leave one event out entirely, train on the rest, test only on the
    # omitted event. With exactly two events this is symmetric — report both directions.
    held_out_results = []
    for held_out_idx, held_out in enumerate(samples):
        train_samples = [s for i, s in enumerate(samples) if i != held_out_idx]
        X_train = np.concatenate([s["X"] for s in train_samples], axis=0)
        y_train = np.concatenate([s["y"] for s in train_samples], axis=0)
        eval_model = LogisticRiskModel().fit(X_train, y_train, feature_names=feature_names)
        test_proba = eval_model.predict_proba(held_out["X"])[:, 1]
        held_out_results.append(
            {
                "heldOutEvent": held_out["event"].name,
                "trainedOnEvents": [s["event"].name for s in train_samples],
                "heldOutRows": int(held_out["X"].shape[0]),
                "heldOutAuc": float(roc_auc_score(held_out["y"], test_proba)),
                "heldOutAccuracy": float((eval_model.predict(held_out["X"]) == held_out["y"]).mean()),
            }
        )

    # The deployed model uses every real event's data — held-out evaluation above already
    # reports how well it's expected to generalize.
    X_all = np.concatenate([s["X"] for s in samples], axis=0)
    y_all = np.concatenate([s["y"] for s in samples], axis=0)
    final_model = LogisticRiskModel().fit(X_all, y_all, feature_names=feature_names)

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    final_model.save(str(MODEL_PATH))

    report = {
        "model_version": MODEL_VERSION,
        "model_type": "logistic_regression",
        "feature_names": feature_names,
        "training_rows": int(X_all.shape[0]),
        "positive_rows": int(y_all.sum()),
        "negative_rows": int((y_all == 0).sum()),
        "events": [
            {
                "name": s["event"].name,
                "observationTimestamp": s["diagnostics"].observation_timestamp,
                "targetTimestamp": s["diagnostics"].target_timestamp,
                "rows": int(s["X"].shape[0]),
                "positiveRows": int(s["y"].sum()),
                "floodReferencePercentage": s["diagnostics"].flood_reference_percentage,
                "selectedSceneIds": list(s["diagnostics"].selected_scene_ids),
            }
            for s in samples
        ],
        "heldOutEventEvaluation": held_out_results,
        "training_data_source": f"real Sentinel-1 GRD + GFD ({len(samples)} real historical events), Bihar-Nepal AOI",
        "not_real_time": True,
        "grid_crs": samples[0]["diagnostics"].crs,
        "grid_scale_m": samples[0]["diagnostics"].label_grid_scale_m,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    main()
