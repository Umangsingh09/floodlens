from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_AOI_GEOJSON = json.dumps(
    {
        "type": "Polygon",
        "coordinates": [
            [
                [83.55, 25.10],
                [88.35, 25.10],
                [88.35, 28.75],
                [87.10, 28.90],
                [86.00, 28.82],
                [84.85, 28.65],
                [84.15, 27.95],
                [83.55, 27.55],
                [83.55, 25.10],
            ]
        ],
    }
)


@dataclass(frozen=True)
class AISettings:
    """AI configuration for the flood-risk pipeline.

    Values are explicit, configurable, and safe for reproducible model runs.
    """

    region_name: str = "bihar-nepal"
    aoi_name: str = "Bihar + southern Nepal flood corridor"
    aoi_geojson: str = DEFAULT_AOI_GEOJSON
    start_date: str = "2016-01-01"
    end_date: str = "2024-12-31"
    satellite_collection: str = "COPERNICUS/S1_GRD"
    satellite_provider: str = "google-earth-engine"
    prediction_horizon_days: int = 7
    model_type: str = "logistic_regression"
    risk_threshold: float = 0.7
    data_dir: str = "ai/data"
    output_dir: str = "ai/outputs"
    dem_enabled: bool = True
    instrument_mode: str = "IW"
    polarizations: tuple[str, ...] = ("VV", "VH")
    earthengine_project: str | None = None
    analysis_interval_days: int = 30
    dem_dataset: str = "USGS/SRTMGL1_003"
    water_threshold_db: float = -12.0
    revisit_days: int = 12

    @property
    def data_root(self) -> Path:
        return Path(__file__).resolve().parents[1] / self.data_dir

    @property
    def output_root(self) -> Path:
        return Path(__file__).resolve().parents[1] / self.output_dir

    @classmethod
    def from_env(cls) -> "AISettings":
        root = Path(__file__).resolve().parents[1]
        env = os.environ

        def get(name: str, default: str | int | float | bool | None):
            raw = env.get(name)
            if raw is None:
                return default
            if isinstance(default, bool):
                return raw.lower() in {"1", "true", "yes", "on"}
            if isinstance(default, int):
                return int(raw)
            if isinstance(default, float):
                return float(raw)
            if isinstance(default, tuple):
                return tuple(part.strip() for part in raw.split(",") if part.strip())
            return raw

        data_dir = get("DATA_DIR", "ai/data")
        output_dir = get("OUTPUT_DIR", "ai/outputs")
        aoi_geojson = get("AOI_GEOJSON", DEFAULT_AOI_GEOJSON)
        earthengine_project = get("EARTH_ENGINE_PROJECT", get("EARTHENGINE_PROJECT", None))

        return cls(
            region_name=get("REGION_NAME", "bihar-nepal"),
            aoi_name=get("AOI_NAME", "Bihar + southern Nepal flood corridor"),
            aoi_geojson=str(aoi_geojson),
            start_date=get("START_DATE", "2016-01-01"),
            end_date=get("END_DATE", "2024-12-31"),
            satellite_collection=get("SATELLITE_COLLECTION", "COPERNICUS/S1_GRD"),
            satellite_provider=get("SATELLITE_PROVIDER", "google-earth-engine"),
            prediction_horizon_days=get("PREDICTION_HORIZON_DAYS", 7),
            model_type=get("MODEL_TYPE", "logistic_regression"),
            risk_threshold=float(get("RISK_THRESHOLD", 0.7)),
            data_dir=str(root / data_dir) if not Path(str(data_dir)).is_absolute() else str(data_dir),
            output_dir=str(root / output_dir) if not Path(str(output_dir)).is_absolute() else str(output_dir),
            dem_enabled=bool(get("DEM_ENABLED", True)),
            instrument_mode=get("SENTINEL1_INSTRUMENT_MODE", "IW"),
            polarizations=get("SENTINEL1_POLARIZATIONS", ("VV", "VH")),
            earthengine_project=earthengine_project,
            analysis_interval_days=int(get("ANALYSIS_INTERVAL_DAYS", 30)),
            dem_dataset=get("DEM_DATASET", "USGS/SRTMGL1_003"),
            water_threshold_db=float(get("WATER_THRESHOLD_DB", -12.0)),
            revisit_days=int(get("REVISIT_DAYS", 12)),
        )


def get_settings() -> AISettings:
    """Return the active AI configuration.

    This keeps the configuration explicit, environment-driven, and free from
    credential leakage.
    """

    return AISettings.from_env()


__all__ = ["AISettings", "DEFAULT_AOI_GEOJSON", "get_settings"]
