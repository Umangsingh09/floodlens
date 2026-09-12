from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.core.config import settings
from app.schemas.risk import RiskResponse
from app.services.raster_service import render_risk_preview_png, resolve_raster_path
from app.services.risk_service import RiskService

logger = logging.getLogger(__name__)

router = APIRouter()
risk_service = RiskService(output_dir=settings.output_dir)


@router.get("/risk/latest", response_model=RiskResponse)
def get_latest_risk() -> RiskResponse:
    prediction = risk_service.latest_prediction()
    if prediction is None:
        raise HTTPException(status_code=404, detail="No prediction artifacts found.")
    return prediction


@router.post("/risk/refresh", response_model=RiskResponse)
def refresh_risk() -> RiskResponse:
    """Run a new live inference pass now and return its result.

    This calls out to live Earth Engine and can take a minute or more (observed ~80s), since it
    scans real scene candidates one at a time. It is synchronous by design so the caller gets a
    definitive result (or a clear error) rather than having to poll; a client should show a
    loading state rather than treat this as a fast call.
    """
    from ai.inference.predict_current_risk import run_prediction

    try:
        run_prediction()
    except Exception as exc:  # noqa: BLE001 - surface any real pipeline failure to the caller
        logger.exception("Live risk refresh failed")
        raise HTTPException(status_code=502, detail=f"Failed to generate a new prediction: {exc}") from exc

    prediction = risk_service.latest_prediction()
    if prediction is None:
        raise HTTPException(status_code=502, detail="Refresh ran but produced no readable prediction artifacts.")
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

    return FileResponse(path=str(raster_path), media_type="image/tiff")


@router.get("/risk/{prediction_id}/preview.png")
def get_risk_preview(prediction_id: str) -> Response:
    try:
        png_bytes = render_risk_preview_png(prediction_id, base_dir=settings.output_dir)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return Response(content=png_bytes, media_type="image/png")
