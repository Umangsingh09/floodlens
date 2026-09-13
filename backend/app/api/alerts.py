from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.schemas.alerts import AlertSubscription, AlertSubscriptionCount, AlertSubscriptionCreate
from app.services.alert_service import AlertService

router = APIRouter()
alert_service = AlertService(output_dir=settings.output_dir)


@router.post("/alerts/subscribe", response_model=AlertSubscription)
def subscribe(data: AlertSubscriptionCreate) -> AlertSubscription:
    return alert_service.create_subscription(data)


@router.delete("/alerts/{subscription_id}", status_code=204)
def unsubscribe(subscription_id: str) -> None:
    if not alert_service.delete_subscription(subscription_id):
        raise HTTPException(status_code=404, detail=f"No subscription found with id '{subscription_id}'.")


@router.get("/alerts/count", response_model=AlertSubscriptionCount)
def get_subscription_count() -> AlertSubscriptionCount:
    return AlertSubscriptionCount(count=alert_service.count())
