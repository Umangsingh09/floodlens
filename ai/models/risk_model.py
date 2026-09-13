from __future__ import annotations

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


class LogisticRiskModel:
    """Simple, interpretable flood-risk baseline using logistic regression.

    Two safeguards beyond a plain `LogisticRegression`, both aimed at the same failure mode —
    a feature seen at a live value the training data never covered:

    1. Features are standardized (zero mean, unit variance) before fitting, so a feature on a
       much larger raw scale than the others (e.g. rainfall in millimeters vs. SAR backscatter
       in dB) can't dominate the linear score just because of its units.
    2. Live features are clipped to the [min, max] range observed during training before
       predicting. A feature with little or no variance in the training data (e.g. a single
       historical snapshot, where rainfall was the same value for every row) gets an
       effectively arbitrary coefficient — nothing in training constrains it. Without clipping,
       a live value far outside that narrow training range multiplied by that arbitrary
       coefficient can push the sigmoid to saturate at exactly 0 or 1 everywhere. Clipping means
       the model only ever answers within the range it actually has evidence for.
    """

    def __init__(self, *, max_iter: int = 2000, class_weight: str | None = "balanced"):
        self.model = LogisticRegression(max_iter=max_iter, class_weight=class_weight)
        self.scaler = StandardScaler()
        self.feature_names: list[str] | None = None
        self.feature_min: np.ndarray | None = None
        self.feature_max: np.ndarray | None = None

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str] | None = None) -> "LogisticRiskModel":
        X_array = np.asarray(X, dtype=float)
        y_array = np.asarray(y, dtype=int)
        if X_array.ndim != 2:
            raise ValueError("Feature matrix X must be 2-D.")
        self.feature_min = X_array.min(axis=0)
        self.feature_max = X_array.max(axis=0)
        X_scaled = self.scaler.fit_transform(X_array)
        self.model.fit(X_scaled, y_array)
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X_array.shape[1])]
        return self

    def _prepare(self, X: np.ndarray) -> np.ndarray:
        X_array = np.asarray(X, dtype=float)
        if X_array.ndim == 1:
            X_array = X_array.reshape(1, -1)
        if self.feature_min is not None and self.feature_max is not None:
            X_array = np.clip(X_array, self.feature_min, self.feature_max)
        return self.scaler.transform(X_array)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(self._prepare(X))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(self._prepare(X))

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> "LogisticRiskModel":
        return joblib.load(path)
