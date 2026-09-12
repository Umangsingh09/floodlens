import json
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_bounds

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from fastapi.testclient import TestClient

from app.main import app
import app.api.risk as risk_api

client = TestClient(app)


def _write_fixture_prediction(tmp_path: Path, prediction_id: str = "20260101T000000Z") -> Path:
    prediction_dir = tmp_path / prediction_id
    prediction_dir.mkdir(parents=True)

    grid = np.array([[0.1, 0.9], [0.4, 0.6]], dtype=np.float32)
    transform = from_bounds(85.0, 26.0, 85.1, 26.1, grid.shape[1], grid.shape[0])
    with rasterio.open(
        prediction_dir / "risk_raster.tif",
        "w",
        driver="GTiff",
        height=grid.shape[0],
        width=grid.shape[1],
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(grid, 1)

    metadata = {
        "regionId": "bihar-nepal",
        "hazard": "flood",
        "risk": {"min": 0.1, "max": 0.9, "mean": 0.5},
        "resolutionMeters": 250.0,
        "crs": "EPSG:4326",
        "bounds": {"west": 85.0, "south": 26.0, "east": 85.1, "north": 26.1},
        "satellite": "Sentinel-1",
        "sourcePassTimestamp": "2026-01-01T00:00:00",
        "predictionTimestamp": "2026-01-01T01:00:00",
        "processingLagSeconds": 3600,
        "predictionHorizonHours": 168,
        "modelId": "logistic-regression",
        "modelVersion": "0.1.0-baseline",
        "alert": {"threshold": 0.7},
    }
    (prediction_dir / "prediction_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")
    return prediction_dir


def test_latest_risk_reads_real_fixture_metadata(tmp_path, monkeypatch):
    _write_fixture_prediction(tmp_path)
    monkeypatch.setattr(risk_api.risk_service, "output_dir", tmp_path)

    response = client.get("/api/risk/latest")
    assert response.status_code == 200
    body = response.json()
    assert body["predictionId"] == "20260101T000000Z"
    assert body["risk"]["mean"] == 0.5
    assert body["alert"]["level"] == "LOW"
    assert body["bounds"] == {"west": 85.0, "south": 26.0, "east": 85.1, "north": 26.1}
    assert body["rasterUrl"] == "/api/risk/20260101T000000Z/raster"
    assert body["previewUrl"] == "/api/risk/20260101T000000Z/preview.png"


def test_latest_risk_returns_404_when_output_dir_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(risk_api.risk_service, "output_dir", tmp_path)
    response = client.get("/api/risk/latest")
    assert response.status_code == 404


def test_raster_endpoint_serves_real_geotiff(tmp_path, monkeypatch):
    _write_fixture_prediction(tmp_path)
    monkeypatch.setattr("app.core.config.settings.output_dir", str(tmp_path))

    response = client.get("/api/risk/20260101T000000Z/raster")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/tiff"
    assert len(response.content) > 0


def test_grid_endpoint_returns_real_cell_values(tmp_path, monkeypatch):
    _write_fixture_prediction(tmp_path)
    monkeypatch.setattr("app.core.config.settings.output_dir", str(tmp_path))

    response = client.get("/api/risk/20260101T000000Z/grid")
    assert response.status_code == 200
    body = response.json()
    assert body["rows"] == 2
    assert body["cols"] == 2
    assert len(body["cells"]) == 4
    values = sorted(cell["value"] for cell in body["cells"])
    assert values == pytest.approx([0.1, 0.4, 0.6, 0.9], abs=1e-6)
    for cell in body["cells"]:
        assert 85.0 <= cell["lon"] <= 85.1
        assert 26.0 <= cell["lat"] <= 26.1


def test_preview_png_endpoint_renders_upsampled_image(tmp_path, monkeypatch):
    _write_fixture_prediction(tmp_path)
    monkeypatch.setattr("app.core.config.settings.output_dir", str(tmp_path))

    response = client.get("/api/risk/20260101T000000Z/preview.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


def test_region_endpoint_returns_real_aoi_config():
    response = client.get("/api/region")
    assert response.status_code == 200
    body = response.json()
    assert body["regionId"]
    assert body["geojson"]["type"] == "Polygon"
    assert body["bounds"]["west"] < body["bounds"]["east"]
    assert body["bounds"]["south"] < body["bounds"]["north"]


def test_events_endpoint_returns_dfo_4507():
    response = client.get("/api/events")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 1
    assert events[0]["dfoId"] == 4507
    assert events[0]["referenceType"] == "remotely sensed historical reference"
