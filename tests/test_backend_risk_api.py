import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.risk import RiskAlert, RiskSummary


client = TestClient(app)


def test_risk_schema_alert_thresholds():
    risk = RiskSummary(min=0.1, max=0.9, mean=0.5)
    alert = RiskAlert(level="HIGH", threshold=0.7)
    assert risk.min == 0.1
    assert alert.level == "HIGH"


def test_health_endpoint_works():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_invalid_prediction_id_returns_404():
    response = client.get("/api/risk/does-not-exist")
    assert response.status_code == 404


def test_raster_path_security_rejects_traversal():
    from app.services.raster_service import resolve_raster_path

    try:
        resolve_raster_path("../../etc/passwd")
        assert False, "Expected ValueError"
    except ValueError:
        pass
