"""
Real scorer — loads the trained model from scoring_model.json.

The model artifact contains:
  - coefficients (intercept + per-feature weights)
  - standardization parameters (mean, std per feature)
  - optimal threshold
  - feature column list

Inference is pure numpy — no sklearn, no joblib, no external ML libs.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from .base import AbstractScorer, FEATURE_NAMES

logger = logging.getLogger(__name__)


class RealScorer(AbstractScorer):
    """
    Production scorer that loads a trained logistic regression
    from a JSON artifact produced by train_model.py.
    """

    def __init__(self) -> None:
        self._intercept: float = 0.0
        self._coefs: Dict[str, float] = {}
        self._means: Dict[str, float] = {}
        self._stds: Dict[str, float] = {}
        self._feature_columns: list[str] = []
        self._threshold: float = 0.5
        self._version: str = "unknown"
        self._base_value: float = 0.304
        self._model_raw: Dict[str, Any] = {}

    # ── AbstractScorer interface ─────────────────────────────

    def load_model(self, model_path: str) -> None:
        """
        Load the scoring_model.json artifact.

        Expected JSON structure (produced by train_model.py):
            {
                "coefficients": {"intercept": float, "features": {name: coef}},
                "standardization": {"mean": {name: val}, "std": {name: val}},
                "feature_columns": [str, ...],
                "threshold": float,
                ...
            }
        """
        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(
                f"Model file not found: {path.resolve()}.  "
                f"Run train_model.py first or check MODEL_PATH in .env"
            )

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._model_raw = data
        self._intercept = float(data["coefficients"]["intercept"])
        self._coefs = {k: float(v) for k, v in data["coefficients"]["features"].items()}
        self._means = {k: float(v) for k, v in data["standardization"]["mean"].items()}
        self._stds = {k: float(v) for k, v in data["standardization"]["std"].items()}
        self._feature_columns = list(data["feature_columns"])
        self._threshold = float(data.get("threshold", 0.5))

        # Derive version from model metadata
        model_type = data.get("model_type", "logistic_regression")
        feature_set = data.get("feature_set", "unknown")
        self._version = f"{model_type}/{feature_set}"

        # Base value = mean P(default) in training set ≈ target_rate
        # Using the intercept through sigmoid as approximation
        # (for a standardized model, sigmoid(intercept) ≈ base rate)
        self._base_value = float(self._sigmoid(np.array([self._intercept]))[0])

        logger.info(
            "Loaded model: %s | %d features | threshold=%.2f | base_value=%.3f",
            self._version,
            len(self._feature_columns),
            self._threshold,
            self._base_value,
        )

    def predict(self, features: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """
        Score a single application.

        1. Standardize each feature: z = (x - mean) / std
        2. Compute logit: intercept + Σ(z_i × coef_i)
        3. Apply sigmoid → P(default)
        4. Compute per-feature logit contributions as XAI values
        """
        if not self._coefs:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # 1. Standardize features
        standardized: Dict[str, float] = {}
        for feat in self._feature_columns:
            raw_value = features.get(feat, 0.0)
            mean = self._means.get(feat, 0.0)
            std = self._stds.get(feat, 1.0)
            standardized[feat] = (raw_value - mean) / std

        # 2. Compute logit
        logit = self._intercept
        for feat in self._feature_columns:
            logit += standardized[feat] * self._coefs[feat]

        # 3. Sigmoid → probability
        probability = float(self._sigmoid(np.array([logit]))[0])
        probability = max(0.001, min(0.999, probability))

        # 4. Per-feature logit contributions (= SHAP values for linear models)
        #    contribution_i = standardized_value_i × coefficient_i
        shap_values: Dict[str, float] = {}
        for feat in self._feature_columns:
            contribution = standardized[feat] * self._coefs[feat]
            shap_values[feat] = round(contribution, 4)

        # Ensure all 8 base features are present in output
        # (even if model uses a subset)
        for feat in FEATURE_NAMES:
            if feat not in shap_values:
                shap_values[feat] = 0.0

        return probability, shap_values

    def get_base_value(self) -> float:
        return self._base_value

    def get_model_version(self) -> str:
        return self._version

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _sigmoid(z: np.ndarray) -> np.ndarray:
        """Numerically stable sigmoid."""
        return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))
