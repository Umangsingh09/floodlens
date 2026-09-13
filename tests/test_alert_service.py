import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import requests
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.risk import RiskAlert, RiskResponse, RiskSummary
from app.services.alert_service import AlertService

client = TestClient(app)


def _risk_response(mean: float, level: str = "LOW") -> RiskResponse:
    return RiskResponse(
        predictionId="p1",
        regionId="bihar-nepal",
        risk=RiskSummary(min=0.0, max=1.0, mean=mean),
        resolutionMeters=250.0,
        crs="EPSG:4326",
        sourcePassTimestamp="2026-01-01T00:00:00",
        predictionTimestamp="2026-01-01T01:00:00",
        processingLagSeconds=3600,
        predictionHorizonHours=168,
        modelId="logistic-regression",
        modelVersion="0.2.0-multi-event",
        alert=RiskAlert(level=level, threshold=0.7),
    )


def test_create_list_and_count_subscriptions(tmp_path):
    service = AlertService(output_dir=tmp_path)
    assert service.count() == 0

    from app.schemas.alerts import AlertSubscriptionCreate

    created = service.create_subscription(AlertSubscriptionCreate(webhookUrl="https://example.com/hook", threshold=0.5))
    assert created.threshold == 0.5
    assert service.count() == 1
    assert service.list_subscriptions()[0].id == created.id


def test_delete_subscription_removes_it(tmp_path):
    service = AlertService(output_dir=tmp_path)
    from app.schemas.alerts import AlertSubscriptionCreate

    created = service.create_subscription(AlertSubscriptionCreate(webhookUrl="https://example.com/hook", threshold=0.5))

    assert service.delete_subscription(created.id) is True
    assert service.count() == 0
    assert service.delete_subscription(created.id) is False


def test_notifies_only_on_a_new_threshold_crossing(tmp_path):
    service = AlertService(output_dir=tmp_path)
    from app.schemas.alerts import AlertSubscriptionCreate

    service.create_subscription(AlertSubscriptionCreate(webhookUrl="https://example.com/hook", threshold=0.5))

    with patch("app.services.alert_service.requests.post") as mock_post:
        mock_post.return_value = MagicMock(raise_for_status=lambda: None)

        # Below threshold: no notification.
        service.check_and_notify(_risk_response(0.3))
        assert mock_post.call_count == 0

        # Crosses above: fires once.
        service.check_and_notify(_risk_response(0.6, level="HIGH"))
        assert mock_post.call_count == 1
        sent_payload = mock_post.call_args.kwargs["json"]
        assert sent_payload["meanRisk"] == 0.6
        assert sent_payload["alertLevel"] == "HIGH"

        # Stays above on the next run: does NOT fire again.
        service.check_and_notify(_risk_response(0.65, level="HIGH"))
        assert mock_post.call_count == 1

        # Drops below, then crosses again: fires a second time.
        service.check_and_notify(_risk_response(0.2))
        service.check_and_notify(_risk_response(0.55, level="HIGH"))
        assert mock_post.call_count == 2


def test_a_broken_webhook_endpoint_does_not_raise(tmp_path):
    service = AlertService(output_dir=tmp_path)
    from app.schemas.alerts import AlertSubscriptionCreate

    service.create_subscription(AlertSubscriptionCreate(webhookUrl="https://example.com/hook", threshold=0.1))

    with patch("app.services.alert_service.requests.post", side_effect=requests.ConnectionError("unreachable")):
        # Must not raise — a subscriber's dead endpoint can't take down the prediction pipeline.
        service.check_and_notify(_risk_response(0.5))


def test_subscribe_endpoint_rejects_an_invalid_url():
    response = client.post("/api/alerts/subscribe", json={"webhookUrl": "not-a-url", "threshold": 0.5})
    assert response.status_code == 422


def test_subscribe_and_unsubscribe_via_the_api(monkeypatch, tmp_path):
    import app.api.alerts as alerts_api

    monkeypatch.setattr(alerts_api.alert_service, "output_dir", tmp_path)
    monkeypatch.setattr(alerts_api.alert_service, "store_path", tmp_path / "alert_subscriptions.json")

    response = client.post("/api/alerts/subscribe", json={"webhookUrl": "https://example.com/hook", "threshold": 0.6})
    assert response.status_code == 200
    subscription_id = response.json()["id"]

    count_response = client.get("/api/alerts/count")
    assert count_response.json()["count"] == 1

    delete_response = client.delete(f"/api/alerts/{subscription_id}")
    assert delete_response.status_code == 204

    missing_response = client.delete(f"/api/alerts/{subscription_id}")
    assert missing_response.status_code == 404
