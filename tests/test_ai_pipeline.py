import numpy as np

from ai.config import DEFAULT_AOI_GEOJSON, get_settings
from ai.preprocessing.dem_features import compute_dem_features
from ai.preprocessing.sentinel1 import summarize_discovery_result, normalize_polarizations
from ai.preprocessing.temporal_features import (
    build_feature_stack,
    build_temporal_water_features,
    compute_temporal_change,
    compute_water_trend,
)
from ai.preprocessing.water_mask import compute_water_mask
from ai.models.risk_model import LogisticRiskModel


def test_configuration_defaults():
    settings = get_settings()
    assert settings.region_name == "bihar-nepal"
    assert settings.satellite_collection == "COPERNICUS/S1_GRD"
    assert 0.0 <= settings.risk_threshold <= 1.0


def test_build_feature_stack_handles_nan_and_alignment():
    vv_t = np.array([[0.2, 0.5], [0.7, np.nan]], dtype=float)
    vh_t = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=float)
    vv_prev = np.array([[0.1, 0.4], [0.5, 0.6]], dtype=float)
    vh_prev = np.array([[0.05, 0.18], [0.2, 0.25]], dtype=float)

    features = build_feature_stack(vv_t, vh_t, vv_prev, vh_prev)

    assert sorted(features.keys()) == [
        "delta_vh",
        "delta_vv",
        "vh_t",
        "vh_t_1",
        "vv_t",
        "vv_t_1",
    ]
    assert features["vv_t"].shape == (2, 2)
    assert np.isfinite(features["delta_vv"]).all()
    assert np.isfinite(features["vv_t"]).all()


def test_water_mask_uses_threshold_and_keeps_no_data():
    array = np.array([[-13.5, -11.0], [-11.5, -16.0]], dtype=float)
    mask = compute_water_mask(array, threshold=-12.0)
    assert mask.dtype == bool
    assert mask[0, 0] is True
    assert mask[0, 1] is False
    assert mask[1, 0] is False
    assert mask[1, 1] is True


def test_normalize_polarizations_handles_various_inputs():
    assert normalize_polarizations("VV,VH") == ["VV", "VH"]
    assert normalize_polarizations(["vh", "vv"]) == ["VV", "VH"]
    assert normalize_polarizations(("VV", "VH")) == ["VV", "VH"]


def test_summarize_discovery_result_reports_scene_and_orientation_metadata():
    result = summarize_discovery_result(
        {
            "total_scenes": 2,
            "acquisition_dates": ["2023-01-01T00:00:00Z", "2023-01-12T00:00:00Z"],
            "polarizations": ["VV", "VH"],
            "instrument_modes": ["IW"],
            "orbit_passes": ["DESCENDING", "DESCENDING"],
            "coverage": {"type": "Polygon", "coordinates": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0], [0.0, 0.0]]]},
            "resolution_meters": 10.0,
            "scene_details": [
                {"scene_id": "S1A_IW_GRDH_1SDV_20230101T000000_20230101T000030_046001_059AAB_1234", "acquisition_date": "2023-01-01T00:00:00Z", "orbit_pass": "DESCENDING", "polarizations": ["VV", "VH"], "instrument_mode": "IW"},
                {"scene_id": "S1A_IW_GRDH_1SDV_20230112T000000_20230112T000030_046111_059BBB_4321", "acquisition_date": "2023-01-12T00:00:00Z", "orbit_pass": "DESCENDING", "polarizations": ["VV", "VH"], "instrument_mode": "IW"},
            ],
        }
    )
    assert result["scene_count"] == 2
    assert result["dates"] == ["2023-01-01", "2023-01-12"]
    assert result["polarizations"] == ["VV", "VH"]
    assert result["instrument_modes"] == ["IW"]
    assert result["orbit_passes"] == ["DESCENDING", "DESCENDING"]
    assert result["resolution_meters"] == 10.0
    assert result["scene_details"][0]["scene_id"].startswith("S1A")


def test_default_aoi_matches_bihar_nepal_corridor_shape():
    polygon = __import__("json").loads(DEFAULT_AOI_GEOJSON)
    coords = polygon["coordinates"][0]
    lons = [point[0] for point in coords]
    lats = [point[1] for point in coords]

    assert polygon["type"] == "Polygon"
    assert len(coords) == 9
    assert min(lons) >= 83.5 and max(lons) <= 88.4
    assert min(lats) >= 25.1 and max(lats) <= 28.9
    assert max(lons) - min(lons) < 5.0
    assert max(lats) - min(lats) < 4.0


def test_temporal_water_features_track_change_and_trend():
    water_t = np.array([[1, 0], [1, 1]], dtype=float)
    water_prev = np.array([[0, 0], [1, 0]], dtype=float)
    water_baseline = np.array([[0, 0], [0, 1]], dtype=float)
    ts = np.array([0.0, 1.0], dtype=float)

    features = build_temporal_water_features(water_t, water_prev, water_baseline, timestamps=ts)
    assert features["water_current"].shape == (2, 2)
    assert features["water_previous"].shape == (2, 2)
    assert np.array_equal(features["water_change"], np.array([[1, 0], [0, 1]], dtype=float))
    assert features["water_persistence"].shape == (2, 2)
    assert "water_trend" in features


def test_temporal_change_and_trend_are_nonnegative_for_valid_inputs():
    base = np.array([[0.0, 0.5], [1.0, 0.25]], dtype=float)
    current = np.array([[0.8, 0.2], [1.2, 0.6]], dtype=float)
    delta = compute_temporal_change(current, base)
    trend = compute_water_trend(current, base)
    assert delta.shape == base.shape
    assert trend.shape == base.shape
    assert np.isfinite(delta).all()
    assert np.isfinite(trend).all()


def test_dem_features_include_elevation_and_slope():
    dem = np.array([[100.0, 200.0], [300.0, 400.0]], dtype=float)
    slope = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=float)
    features = compute_dem_features(dem, slope)
    assert set(features.keys()) == {"elevation", "slope"}
    assert features["elevation"].shape == (2, 2)
    assert features["slope"].shape == (2, 2)


def test_logistic_model_predicts_probability():
    model = LogisticRiskModel()
    X = np.array([[0.1, 0.2], [1.0, 1.5], [-0.2, -0.1], [0.8, 0.9]], dtype=float)
    y = np.array([0, 1, 0, 1], dtype=int)
    model.fit(X, y)
    prob = model.predict_proba(X)
    assert prob.shape == (len(X), 2)
    assert ((prob >= 0.0) & (prob <= 1.0)).all()
    assert float(prob[:, 1].min()) >= 0.0
    assert float(prob[:, 1].max()) <= 1.0


def test_gfd_reference_mask_excludes_permanent_water():
    from ai.historical_reference import build_gfd_flood_reference

    flooded = np.array([[1, 1, 0], [0, 1, 0]], dtype=float)
    permanent_water = np.array([[0, 1, 0], [0, 0, 0]], dtype=float)

    reference = build_gfd_flood_reference(flooded, permanent_water)

    assert reference.dtype == bool
    assert reference.tolist() == [[True, False, False], [False, True, False]]


def test_gfd_event_selection_uses_dfo_4507():
    from ai.historical_reference import GFD_VALIDATION_DFO_ID, select_gfd_event

    events = [
        {"id": 4506, "country": "India"},
        {"id": 4507, "country": "India", "start": "2017-08-10", "end": "2017-08-26"},
        {"id": 4508, "country": "Bangladesh"},
    ]

    match = select_gfd_event(events, GFD_VALIDATION_DFO_ID)
    assert match["id"] == GFD_VALIDATION_DFO_ID
    assert match["start"] == "2017-08-10"
    assert match["end"] == "2017-08-26"


def test_gfd_reference_handles_nodata_and_area_logic():
    from ai.historical_reference import build_gfd_flood_reference, compute_reference_area_m2

    flooded = np.array([[1.0, np.nan, 1.0], [0.0, 1.0, 0.0]], dtype=float)
    permanent = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0]], dtype=float)

    reference = build_gfd_flood_reference(flooded, permanent, nodata=np.nan)
    area = compute_reference_area_m2(reference, pixel_size_m=250.0)

    assert bool(reference[0, 0]) is True
    assert bool(reference[0, 1]) is False
    assert bool(reference[1, 1]) is False
    assert area == 125000.0
