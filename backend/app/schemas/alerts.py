from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class AlertSubscriptionCreate(BaseModel):
    """A webhook: any URL that accepts an HTTP POST — a Slack/Discord incoming webhook, a
    Zapier/IFTTT catch hook, or a custom endpoint. No email/SMS provider is configured for this
    deployment, so a webhook is the one notification channel that needs no external account."""

    webhookUrl: HttpUrl
    threshold: float = Field(..., ge=0.0, le=1.0, description="Notify when mean risk crosses this, 0..1")


class AlertSubscription(BaseModel):
    id: str
    webhookUrl: str
    threshold: float
    createdAt: str


class AlertSubscriptionCount(BaseModel):
    count: int
