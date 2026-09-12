from __future__ import annotations

import numpy as np

from ai.preprocessing.real_gee_sampling import (
    GridSpec,
    _has_real_signal,
    aggregate_feature_to_label_grid,
    select_temporal_observation_scenes,
)
from ai.training.dataset import (
    DatasetConfig,
    TemporalSample,
    apply_dataset_quality_checks,
    build_future_flood_dataset,
    split_temporal_dataset,
)


def test_future_flood_target_is_7_days_after_observation_and_excludes_permanent_water():
    config = DatasetConfig(
        prediction_horizon_days=7,
        observation_window_days=(-2, 0),
        feature_resolution_m=10.0,
        label_resolution_m=250.0,
    )

    observation = np.array([[0.2, -12.0], [0.1, -10.0]], dtype=np.float32)
    previous = np.array([[0.1, -11.0], [0.0, -9.0]], dtype=np.float32)
    label = np.array([[1, 0], [0, 0]], dtype=np.float32)
    permanent_water = np.array([[0, 1], [0, 0]], dtype=np.float32)

    dataset = build_future_flood_dataset(
        observation_timestamps=["2024-01-01", "2024-01-03"],
        feature_arrays={
            "vv_t": observation,
            "vh_t": observation,
            "vv_t_1": previous,
            "vh_t_1": previous,
        },
        flood_reference=label,
        permanent_water=permanent_water,
        config=config,
    )

    assert len(dataset.samples) == 2
    assert dataset.samples[0].observation_timestamp.isoformat() == "2024-01-01T00:00:00"
    assert dataset.samples[0].target_timestamp.isoformat() == "2024-01-08T00:00:00"
    assert dataset.samples[0].label.shape == (2, 2)
    assert dataset.samples[0].label.dtype == np.bool_
    assert dataset.samples[0].label.tolist() == [[True, False], [False, False]]
    assert dataset.metadata.prediction_horizon_days == 7
    assert dataset.metadata.validation_event_ids == (4507,)


def test_temporal_split_is_chronological_and_keeps_target_order():
    timestamps = [
        "2024-01-01",
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
        "2024-01-06",
    ]
    samples = [
        TemporalSample(
            observation_timestamp=np.datetime64(ts, "D"),
            target_timestamp=np.datetime64(ts, "D") + np.timedelta64(7, "D"),
            feature_map={"vv_t": np.array([[1.0]], dtype=np.float32)},
            label=np.array([[1]], dtype=np.bool_),
            quality_checks={},
        )
        for ts in timestamps
    ]

    split = split_temporal_dataset(samples, ratios=(0.6, 0.2, 0.2))

    assert [len(split["train"]), len(split["validation"]), len(split["test"])] == [4, 1, 1]
    assert split["train"][-1].observation_timestamp.isoformat() == "2024-01-04T00:00:00"
    assert split["validation"][0].observation_timestamp.isoformat() == "2024-01-05T00:00:00"
    assert split["test"][0].observation_timestamp.isoformat() == "2024-01-06T00:00:00"


def test_quality_checks_reject_nan_in_features_or_invalid_label_classes():
    sample = TemporalSample(
        observation_timestamp=np.datetime64("2024-01-01", "D"),
        target_timestamp=np.datetime64("2024-01-08", "D"),
        feature_map={"vv_t": np.array([[np.nan, 1.0]], dtype=np.float32)},
        label=np.array([[2, 0]], dtype=np.int16),
        quality_checks={},
    )

    problems = apply_dataset_quality_checks(sample, strict=True)
    assert "vv_t_nan" in problems or "invalid_label_values" in problems


def test_aggregation_uses_mean_on_the_training_grid():
    data = np.arange(16, dtype=np.float32).reshape(4, 4)
    aggregated = aggregate_feature_to_label_grid(data, block_h=2, block_w=2, method="mean")
    expected = np.array([[2.5, 4.5], [10.5, 12.5]], dtype=np.float32)
    assert aggregated.shape == (2, 2)
    np.testing.assert_allclose(aggregated, expected)


def test_temporal_selection_rejects_future_scenes():
    scene_times = ["2024-01-01", "2024-01-02", "2024-01-09"]
    selected = select_temporal_observation_scenes(scene_times, "2024-01-08", count=2, max_lookback_days=30)
    assert [dt.isoformat() for dt in selected] == ["2024-01-01T00:00:00", "2024-01-02T00:00:00"]


def test_temporal_selection_uses_unique_acquisition_dates():
    scene_times = [
        "2024-01-01T00:00:00",
        "2024-01-01T12:00:00",
        "2024-01-02T00:00:00",
        "2024-01-03T00:00:00",
    ]
    selected = select_temporal_observation_scenes(scene_times, "2024-01-04", count=2, max_lookback_days=30)
    assert [dt.isoformat() for dt in selected] == ["2024-01-02T00:00:00", "2024-01-03T00:00:00"]


def test_temporal_selection_excludes_zero_filled_missing_signal():
    scene_times = [
        "2024-01-01T00:00:00",
        "2024-01-02T00:00:00",
        "2024-01-03T00:00:00",
    ]
    signal_presence = [False, True, True]
    selected = select_temporal_observation_scenes(
        scene_times, "2024-01-04", count=2, max_lookback_days=30, signal_presence=signal_presence
    )
    assert [dt.isoformat() for dt in selected] == ["2024-01-02T00:00:00", "2024-01-03T00:00:00"]
    assert not _has_real_signal(np.zeros((2, 2), dtype=np.float32), np.zeros((2, 2), dtype=np.float32))
    assert _has_real_signal(
        np.array([[0.0, -12.0], [0.0, -8.0]], dtype=np.float32),
        np.array([[0.0, -18.0], [0.0, -5.0]], dtype=np.float32),
    )


def test_grid_spec_and_split_defaults_are_documented_and_stable():
    grid = GridSpec()
    assert grid.crs == "EPSG:32645"
    assert grid.scale_m == 250.0
    assert grid.feature_scale_m == 10.0
    assert grid.label_scale_m == 250.0
