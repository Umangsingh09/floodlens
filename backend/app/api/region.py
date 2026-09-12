from __future__ import annotations

from fastapi import APIRouter

from app.schemas.region import RegionResponse
from app.services.region_service import get_region_info

router = APIRouter()


@router.get("/region", response_model=RegionResponse)
def get_region() -> RegionResponse:
    return get_region_info()
