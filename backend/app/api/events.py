from __future__ import annotations

from fastapi import APIRouter

from app.schemas.events import HistoricalEvent
from app.services.events_service import list_historical_events

router = APIRouter()


@router.get("/events", response_model=list[HistoricalEvent])
def get_events() -> list[HistoricalEvent]:
    return list_historical_events()
