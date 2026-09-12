from __future__ import annotations

from app.schemas.events import HistoricalEvent


def list_historical_events() -> list[HistoricalEvent]:
    from ai.historical_reference import create_gfd_validation_event_metadata

    summary = create_gfd_validation_event_metadata()
    return [
        HistoricalEvent(
            dfoId=summary.dfo_id,
            imageId=summary.image_id,
            startDate=summary.start_date,
            endDate=summary.end_date,
            primaryCountry=summary.primary_country,
            countries=summary.countries,
            resolutionMeters=summary.resolution_m,
            referenceType=summary.reference_type,
        )
    ]
