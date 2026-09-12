from __future__ import annotations

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression


class LogisticRiskModel:
    """Simple, interpretable flood-risk baseline using logistic regression."""

    def __init__(self, *, max_iter: int = 2000, class_weight: str | None = "balanced"):
        self.model = LogisticRegression(max_iter=max_iter, class_weight=class_weight)
        self.feature_names: list[str] | None = None

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: list[str] | None = None) -> "LogisticRiskModel":
        X_array = np.asarray(X, dtype=float)
        y_array = np.asarray(y, dtype=int)
        if X_array.ndim != 2:
            raise ValueError("Feature matrix X must be 2-D.")
        self.model.fit(X_array, y_array)
        self.feature_names = feature_names or [f"feature_{i}" for i in range(X_array.shape[1])]
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X_array = np.asarray(X, dtype=float)
        if X_array.ndim == 1:
            X_array = X_array.reshape(1, -1)
        return self.model.predict_proba(X_array)

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(np.asarray(X, dtype=float))

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> "LogisticRiskModel":
        return joblib.load(path)
