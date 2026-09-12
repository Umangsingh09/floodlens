from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Mapping, Sequence

import numpy as np

from ai.historical_reference import (
    GFD_REFERENCE_RESOLUTION_M,
    GFD_VALIDATION_DFO_ID,
    build_gfd_flood_reference,
)


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, np.datetime64):
        return datetime.fromisoformat(str(value))
    if isinstance(value, str):
        return datetime.fromisoformat(value)
    raise TypeError(f"Unsupported timestamp type: {type(value)!r}")


def _align_array_to_target(array: np.ndarray, target_shape: tuple[int, int]) -> np.ndarray:
    aligned = np.asarray(array, dtype=np.float32)
    if aligned.shape == target_shape:
        return aligned
    if aligned.ndim != 2:
        raise ValueError(f"Expected a 2D feature array, got shape {aligned.shape!r}.")

    height, width = target_shape
    if aligned.shape[0] < height or aligned.shape[1] < width:
        padded = np.full(target_shape, np.nan, dtype=np.float32)
        rows = min(aligned.shape[0], height)
        cols = min(aligned.shape[1], width)
        padded[:rows, :cols] = aligned[:rows, :cols]
        return padded

    if aligned.shape[0] % height == 0 and aligned.shape[1] % width == 0:
        block_h = aligned.shape[0] // height
        block_w = aligned.shape[1] // width
        return aligned.reshape(height, block_h, width, block_w).mean(axis=(1, 3))

    row_step = max(1, aligned.shape[0] // height)
    col_step = max(1, aligned.shape[1] // width)
    window = aligned[: height * row_step, : width * col_step]
    return window.reshape(height, row_step, width, col_step).mean(axis=(1, 3))


@dataclass(frozen=True)
class DatasetConfig:
    prediction_horizon_days: int = 7
    observation_window_days: tuple[int, int] = (-2, 0)
    feature_resolution_m: float = 10.0
    label_resolution_m: float = GFD_REFERENCE_RESOLUTION_M
    common_crs: str = "EPSG:32645"
    validation_event_ids: tuple[int, ...] = (GFD_VALIDATION_DFO_ID,)
    target_label_values: tuple[int, ...] = (0, 1)
    temporal_split_ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)

    def __post_init__(self) -> None:
        if self.prediction_horizon_days <= 0:
            raise ValueError("prediction_horizon_days must be positive.")
        if len(self.observation_window_days) != 2:
            raise ValueError("observation_window_days must have exactly two values.")
        total = sum(self.temporal_split_ratios)
        if not np.isclose(total, 1.0):
            raise ValueError("temporal_split_ratios must sum to 1.0.")


@dataclass(frozen=True)
class DatasetMetadata:
    feature_resolution_m: float
    label_resolution_m: float
    prediction_horizon_days: int
    observation_window_days: tuple[int, int]
    common_crs: str
    feature_names: tuple[str, ...]
    split_strategy: str = "temporal_chronological"
    validation_event_ids: tuple[int, ...] = (GFD_VALIDATION_DFO_ID,)
    label_definition: str = "flooded == 1 and jrc_perm_water == 0"


@dataclass
class TemporalSample:
    observation_timestamp: datetime
    target_timestamp: datetime
    feature_map: dict[str, np.ndarray]
    label: np.ndarray
    quality_checks: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.observation_timestamp = _as_datetime(self.observation_timestamp)
        self.target_timestamp = _as_datetime(self.target_timestamp)

    @property
    def is_valid(self) -> bool:
        return not self.quality_checks


@dataclass
class TrainingDataset:
    samples: list[TemporalSample]
    metadata: DatasetMetadata


def _normalize_feature_map(feature_map: Mapping[str, np.ndarray], label_shape: tuple[int, int]) -> dict[str, np.ndarray]:
    normalized: dict[str, np.ndarray] = {}
    for key, value in feature_map.items():
        array = np.asarray(value, dtype=np.float32)
        if array.ndim == 0:
            array = array.reshape(1, 1)
        if array.ndim == 1:
            array = array.reshape(1, -1)
        if array.shape != label_shape:
            array = _align_array_to_target(array, label_shape)
        normalized[key] = np.nan_to_num(array, nan=0.0, posinf=0.0, neginf=0.0)
    return normalized


def _build_label_mask(flood_reference: np.ndarray, permanent_water: np.ndarray, *, nodata: float | None = None) -> np.ndarray:
    reference = build_gfd_flood_reference(
        np.asarray(flood_reference, dtype=np.float32),
        np.asarray(permanent_water, dtype=np.float32),
        nodata=nodata,
    )
    return np.asarray(reference, dtype=np.bool_)


def build_future_flood_dataset(
    *,
    observation_timestamps: Sequence[Any],
    feature_arrays: Mapping[str, np.ndarray],
    flood_reference: np.ndarray,
    permanent_water: np.ndarray,
    config: DatasetConfig | None = None,
    reference_name: str = "GFD historical flood reference",
) -> TrainingDataset:
    """Construct a future-flood dataset where X(t) is observed and Y(t+7) is the future target.

    The observation timestamp is the source of X(t), while the target timestamp is 7 days later.
    The label intentionally represents the future event, not the current water state.
    """
    cfg = config or DatasetConfig()
    label_mask = _build_label_mask(flood_reference, permanent_water)
    feature_names = tuple(feature_arrays.keys())

    samples: list[TemporalSample] = []
    for timestamp in observation_timestamps:
        obs_dt = _as_datetime(timestamp)
        target_dt = obs_dt + timedelta(days=cfg.prediction_horizon_days)
        aligned_features = _normalize_feature_map(feature_arrays, label_mask.shape)
        sample = TemporalSample(
            observation_timestamp=obs_dt,
            target_timestamp=target_dt,
            feature_map=aligned_features,
            label=np.asarray(label_mask, dtype=np.bool_),
            metadata={
                "reference_name": reference_name,
                "feature_resolution_m": cfg.feature_resolution_m,
                "label_resolution_m": cfg.label_resolution_m,
                "target_horizon_days": cfg.prediction_horizon_days,
                "observation_window_days": cfg.observation_window_days,
                "common_crs": cfg.common_crs,
            },
        )
        sample.quality_checks = apply_dataset_quality_checks(sample, strict=True)
        samples.append(sample)

    metadata = DatasetMetadata(
        feature_resolution_m=cfg.feature_resolution_m,
        label_resolution_m=cfg.label_resolution_m,
        prediction_horizon_days=cfg.prediction_horizon_days,
        observation_window_days=cfg.observation_window_days,
        common_crs=cfg.common_crs,
        feature_names=feature_names,
        validation_event_ids=cfg.validation_event_ids,
        split_strategy="temporal_chronological",
    )
    return TrainingDataset(samples=samples, metadata=metadata)


def apply_dataset_quality_checks(sample: TemporalSample, *, strict: bool = True) -> dict[str, Any]:
    """Return a dictionary of data-quality issues for one sample."""
    problems: dict[str, Any] = {}

    if not isinstance(sample.label, np.ndarray):
        problems["invalid_label_object"] = True
        return problems

    label_array = np.asarray(sample.label)
    if label_array.ndim != 2:
        problems["label_dim"] = label_array.shape
    if not np.isin(label_array, [0, 1, True, False]).all():
        problems["invalid_label_values"] = np.unique(label_array)

    for name, feature in sample.feature_map.items():
        feature_array = np.asarray(feature, dtype=np.float32)
        if feature_array.ndim != 2:
            problems[f"{name}_dim"] = feature_array.shape
        if not np.isfinite(feature_array).all():
            problems[f"feature_nan"] = {name: True}
            problems[f"{name}_nan"] = True
        if label_array.shape != feature_array.shape:
            problems[f"{name}_shape_mismatch"] = (feature_array.shape, label_array.shape)

    target_delta = sample.target_timestamp - sample.observation_timestamp
    expected_horizon = sample.metadata.get("target_horizon_days", 7)
    if target_delta.days != expected_horizon:
        problems["prediction_horizon_mismatch"] = target_delta.days

    if sample.observation_timestamp is None or sample.target_timestamp is None:
        problems["invalid_timestamps"] = True

    return problems


def split_temporal_dataset(
    samples: Sequence[TemporalSample],
    *,
    ratios: tuple[float, float, float] | None = None,
) -> dict[str, list[TemporalSample]]:
    """Split a chronological dataset into train/validation/test sets without random pixel leakage."""
    ratios = ratios or (0.7, 0.15, 0.15)
    n = len(samples)
    if n == 0:
        return {"train": [], "validation": [], "test": []}

    train_n = int(round(n * ratios[0]))
    val_n = int(round(n * ratios[1]))
    test_n = n - train_n - val_n
    if test_n < 1 and n > 1:
        test_n = 1
        val_n = max(0, n - train_n - test_n)
    if train_n < 1 and n > 1:
        train_n = 1

    train_end = min(train_n, n)
    val_end = min(train_end + val_n, n)
    train = list(samples[:train_end])
    validation = list(samples[train_end:val_end])
    test = list(samples[val_end:])
    return {"train": train, "validation": validation, "test": test}


__all__ = [
    "DatasetConfig",
    "DatasetMetadata",
    "TemporalSample",
    "TrainingDataset",
    "apply_dataset_quality_checks",
    "build_future_flood_dataset",
    "split_temporal_dataset",
]
