from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from app.schemas.risk import RiskAlert, RiskBounds, RiskHistoryPoint, RiskResponse, RiskSummary

logger = logging.getLogger(__name__)


class RiskService:
    """Service for loading the latest prediction metadata and generating API payloads."""

    def __init__(self, *, output_dir: str | Path | None = None):
        self.output_dir = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parents[3] / "ai" / "outputs"

    def load_metadata(self, prediction_id: str) -> dict:
        metadata_file = self.output_dir / prediction_id / "prediction_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"No metadata found for prediction '{prediction_id}'.")
        return json.loads(metadata_file.read_text(encoding="utf-8"))

    def latest_prediction(self) -> RiskResponse | None:
        if not self.output_dir.exists():
            logger.warning("Prediction output directory does not exist: %s", self.output_dir)
            return None
        candidates = sorted(p for p in self.output_dir.iterdir() if p.is_dir())
        if not candidates:
            logger.warning("No prediction directories found under: %s", self.output_dir)
            return None
        latest = candidates[-1]
        try:
            metadata = self.load_metadata(latest.name)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            logger.error("Failed to load latest prediction metadata for '%s': %s", latest.name, exc)
            return None
        return self._build_response(latest.name, metadata)

    def _build_response(self, prediction_id: str, metadata: dict) -> RiskResponse:
        summary = RiskSummary(
            min=float(metadata.get("risk", {}).get("min", 0.0)),
            max=float(metadata.get("risk", {}).get("max", 1.0)),
            mean=float(metadata.get("risk", {}).get("mean", 0.0)),
        )

        threshold = float(metadata.get("alert", {}).get("threshold", 0.7))
        level = self.calculate_alert(summary.mean, threshold)
        alert = RiskAlert(level=level, threshold=threshold)

        bounds_raw = metadata.get("bounds")
        bounds = RiskBounds(**bounds_raw) if bounds_raw else None

        raster_path = self.output_dir / prediction_id / "risk_raster.tif"
        has_raster = raster_path.exists()

        return RiskResponse(
            predictionId=prediction_id,
            regionId=metadata.get("regionId", "bihar-nepal"),
            hazard=metadata.get("hazard", "flood"),
            risk=summary,
            resolutionMeters=float(metadata.get("resolutionMeters", 10.0)),
            crs=metadata.get("crs", "EPSG:4326"),
            bounds=bounds,
            satellite=metadata.get("satellite", "Sentinel-1"),
            sourcePassTimestamp=metadata.get("sourcePassTimestamp", datetime.now(timezone.utc).isoformat()),
            predictionTimestamp=metadata.get("predictionTimestamp", datetime.now(timezone.utc).isoformat()),
            processingLagSeconds=int(metadata.get("processingLagSeconds", 0)),
            predictionHorizonHours=int(metadata.get("predictionHorizonHours", 0)),
            modelId=metadata.get("modelId", "logistic-regression"),
            modelVersion=metadata.get("modelVersion", "0.1.0"),
            alert=alert,
            rasterUrl=f"/api/risk/{prediction_id}/raster" if has_raster else None,
            previewUrl=f"/api/risk/{prediction_id}/preview.png" if has_raster else None,
            gridUrl=f"/api/risk/{prediction_id}/grid" if has_raster else None,
            observationWindowScenes=metadata.get("observationWindowScenes"),
            gridShape=metadata.get("gridShape"),
            weatherContext=metadata.get("weatherContext"),
            note=metadata.get("note"),
        )

    def list_history(self, *, limit: int = 20) -> list[RiskHistoryPoint]:
        if not self.output_dir.exists():
            return []
        candidates = sorted(p for p in self.output_dir.iterdir() if p.is_dir())
        points: list[RiskHistoryPoint] = []
        for candidate in candidates[-limit:]:
            try:
                metadata = self.load_metadata(candidate.name)
            except (FileNotFoundError, json.JSONDecodeError):
                continue
            mean = float(metadata.get("risk", {}).get("mean", 0.0))
            threshold = float(metadata.get("alert", {}).get("threshold", 0.7))
            points.append(
                RiskHistoryPoint(
                    predictionId=candidate.name,
                    predictionTimestamp=metadata.get("predictionTimestamp", ""),
                    mean=mean,
                    alertLevel=self.calculate_alert(mean, threshold),
                )
            )
        return points

    @staticmethod
    def calculate_alert(mean_risk: float, threshold: float) -> str:
        if mean_risk >= 0.85:
            return "VERY_HIGH"
        if mean_risk >= 0.7:
            return "HIGH"
        if mean_risk >= max(0.4, threshold):
            return "MODERATE"
        if mean_risk >= threshold:
            return "HIGH"
        return "LOW"
