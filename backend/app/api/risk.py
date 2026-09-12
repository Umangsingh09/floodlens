from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.risk import RiskResponse
from app.services.raster_service import resolve_raster_path
from app.services.risk_service import RiskService

router = APIRouter()
risk_service = RiskService(output_dir=settings.output_dir)


@router.get("/risk/latest", response_model=RiskResponse)
def get_latest_risk() -> RiskResponse:
    prediction = risk_service.latest_prediction()
    if prediction is None:
        raise HTTPException(status_code=404, detail="No prediction artifacts found.")
    return prediction


@router.get("/risk/{prediction_id}", response_model=RiskResponse)
def get_risk_by_id(prediction_id: str) -> RiskResponse:
    try:
        metadata = risk_service.load_metadata(prediction_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return risk_service._build_response(prediction_id, metadata)


@router.get("/risk/{prediction_id}/raster")
def get_risk_raster(prediction_id: str) -> FileResponse:
    try:
        raster_path = resolve_raster_path(prediction_id, base_dir=settings.output_dir)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not raster_path.exists():
        raise HTTPException(status_code=404, detail="Raster is missing for the requested prediction ID.")

    return FileResponse(path=str(raster_path), media_type="image/tiff")
