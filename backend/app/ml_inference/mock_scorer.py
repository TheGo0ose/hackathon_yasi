"""
Mock scorer — deterministic heuristic that produces realistic-looking
predictions and SHAP values so the frontend team can build UI immediately.

The heuristic is NOT random: identical inputs always produce identical
outputs, which makes frontend snapshot testing reliable.
"""

from __future__ import annotations

import math
from typing import Dict, Tuple

from .base import AbstractScorer, FEATURE_NAMES


# "Normal" applicant profile — deviations from these values drive SHAP
_BASELINE: Dict[str, float] = {
    "age": 35.0,
    "monthly_income": 35_000.0,
    "employment_years": 6.0,
    "loan_amount": 400_000.0,
    "loan_term_months": 36.0,
    "interest_rate": 28.0,
    "past_due_30d": 0.0,
    "inquiries_6m": 1.0,
}

# How strongly each feature's deviation affects the log-odds
_WEIGHTS: Dict[str, float] = {
    "age": -0.025,              # older → less risky
    "monthly_income": -0.000015, # higher income → less risky
    "employment_years": -0.06,   # longer tenure → less risky
    "loan_amount": 0.0000025,    # bigger loan → more risky
    "loan_term_months": 0.012,   # longer term → slightly more risky
    "interest_rate": 0.045,      # higher rate → more risky
    "past_due_30d": 0.35,        # delinquencies → much more risky
    "inquiries_6m": 0.15,        # many inquiries → more risky
}

# Approximate SHAP sensitivity per unit deviation from baseline
_SHAP_SCALE: Dict[str, float] = {
    "age": 0.003,
    "monthly_income": 0.0000035,
    "employment_years": 0.015,
    "loan_amount": 0.0000005,
    "loan_term_months": 0.004,
    "interest_rate": 0.012,
    "past_due_30d": 0.09,
    "inquiries_6m": 0.045,
}

# Features where higher value means LOWER risk (negative SHAP direction)
_NEGATIVE_DIRECTION = {"age", "monthly_income", "employment_years"}


class MockScorer(AbstractScorer):
    """
    Deterministic mock scorer.

    Produces:
    - A plausible probability_of_default driven by simple heuristics.
    - SHAP-like feature contributions that react to input changes,
      so the frontend can render waterfall / bar charts immediately.
    """

    # ── AbstractScorer interface ─────────────────────────────

    def load_model(self, model_path: str) -> None:
        """No-op — mock needs no external model file."""
        pass

    def predict(self, features: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """
        Produce (probability_of_default, shap_values_dict).

        The probability is computed via a logistic function applied to
        a weighted sum of deviations from the baseline profile.
        """
        log_odds = 0.0
        shap_values: Dict[str, float] = {}

        for feat in FEATURE_NAMES:
            value = features.get(feat, _BASELINE[feat])
            delta = value - _BASELINE[feat]

            # Accumulate log-odds for probability
            log_odds += delta * _WEIGHTS[feat]

            # Compute a SHAP-like contribution
            sign = -1.0 if feat in _NEGATIVE_DIRECTION else 1.0
            shap_values[feat] = round(sign * delta * _SHAP_SCALE[feat], 4)

        # Shift log-odds so that the baseline profile gives P ≈ 0.304
        #   logit(0.304) ≈ -0.828
        log_odds += -0.828

        probability = self._sigmoid(log_odds)
        probability = max(0.01, min(0.99, probability))

        return probability, shap_values

    def get_base_value(self) -> float:
        """Mean P(default) in the training dataset."""
        return 0.304

    def get_model_version(self) -> str:
        return "mock-v0.1.0"

    # ── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _sigmoid(x: float) -> float:
        """Numerically stable sigmoid."""
        if x >= 0:
            return 1.0 / (1.0 + math.exp(-x))
        exp_x = math.exp(x)
        return exp_x / (1.0 + exp_x)
