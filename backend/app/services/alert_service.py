from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from app.schemas.alerts import AlertSubscription, AlertSubscriptionCreate
from app.schemas.risk import RiskResponse

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT_SECONDS = 8


class AlertService:
    """Threshold-crossing alerts delivered by webhook — no email/SMS provider is configured for
    this deployment, so a webhook (Slack/Discord incoming webhook, Zapier, a custom endpoint) is
    the one channel that needs no external account to actually work.

    Subscriptions are a single JSON file next to the prediction outputs — this project has no
    database, and a small hackathon-scale subscriber list doesn't need one yet.
    """

    def __init__(self, *, output_dir: str | Path | None = None):
        self.output_dir = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parents[3] / "ai" / "outputs"
        self.store_path = self.output_dir / "alert_subscriptions.json"

    def _load_raw(self) -> list[dict[str, Any]]:
        if not self.store_path.exists():
            return []
        try:
            return json.loads(self.store_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.error("Alert subscription store is corrupt; treating as empty: %s", self.store_path)
            return []

    def _save_raw(self, subscriptions: list[dict[str, Any]]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(subscriptions, indent=2), encoding="utf-8")

    def list_subscriptions(self) -> list[AlertSubscription]:
        return [
            AlertSubscription(id=s["id"], webhookUrl=s["webhookUrl"], threshold=s["threshold"], createdAt=s["createdAt"])
            for s in self._load_raw()
        ]

    def count(self) -> int:
        return len(self._load_raw())

    def create_subscription(self, data: AlertSubscriptionCreate) -> AlertSubscription:
        subscriptions = self._load_raw()
        record = {
            "id": uuid.uuid4().hex,
            "webhookUrl": str(data.webhookUrl),
            "threshold": data.threshold,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            # Tracks whether the last known prediction was at/above this subscription's
            # threshold, so a notification fires only on a NEW crossing — not every single
            # scheduled run while risk stays elevated.
            "lastState": None,
        }
        subscriptions.append(record)
        self._save_raw(subscriptions)
        return AlertSubscription(id=record["id"], webhookUrl=record["webhookUrl"], threshold=record["threshold"], createdAt=record["createdAt"])

    def delete_subscription(self, subscription_id: str) -> bool:
        subscriptions = self._load_raw()
        remaining = [s for s in subscriptions if s["id"] != subscription_id]
        if len(remaining) == len(subscriptions):
            return False
        self._save_raw(remaining)
        return True

    def check_and_notify(self, prediction: RiskResponse) -> None:
        """Call after every real prediction, with the fully-built RiskResponse (its `alert.level`
        is computed there, from the actual configured threshold — not re-derived here). Never
        raises — a webhook failure or a subscriber's broken endpoint must not take down the
        prediction pipeline that called this."""
        subscriptions = self._load_raw()
        if not subscriptions:
            return

        mean_risk = prediction.risk.mean
        changed = False

        for subscription in subscriptions:
            is_above = mean_risk >= subscription["threshold"]
            was_above = subscription.get("lastState") == "above"
            if is_above and not was_above:
                self._send_webhook(subscription, prediction, mean_risk)
            if is_above != was_above:
                subscription["lastState"] = "above" if is_above else "below"
                changed = True

        if changed:
            self._save_raw(subscriptions)

    def _send_webhook(self, subscription: dict[str, Any], prediction: RiskResponse, mean_risk: float) -> None:
        payload = {
            "event": "floodlens.risk_threshold_crossed",
            "predictionId": prediction.predictionId,
            "regionId": prediction.regionId,
            "meanRisk": mean_risk,
            "threshold": subscription["threshold"],
            "alertLevel": prediction.alert.level,
            "predictionTimestamp": prediction.predictionTimestamp,
        }
        try:
            response = requests.post(subscription["webhookUrl"], json=payload, timeout=WEBHOOK_TIMEOUT_SECONDS)
            response.raise_for_status()
            logger.info("Sent alert webhook for subscription %s (mean_risk=%.3f)", subscription["id"], mean_risk)
        except requests.RequestException:
            logger.exception("Failed to deliver alert webhook for subscription %s", subscription["id"])


__all__ = ["AlertService"]
