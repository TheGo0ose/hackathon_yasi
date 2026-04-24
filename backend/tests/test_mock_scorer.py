"""
Tests for the MockScorer — verifies determinism, output ranges, and SHAP structure.
"""

from app.ml_inference import MockScorer
from app.ml_inference.base import FEATURE_NAMES


def _make_features(**overrides) -> dict:
    """Build a feature dict with sensible defaults, overriding as needed."""
    base = {
        "age": 35.0,
        "monthly_income": 35_000.0,
        "employment_years": 6.0,
        "loan_amount": 400_000.0,
        "loan_term_months": 36.0,
        "interest_rate": 28.0,
        "past_due_30d": 0.0,
        "inquiries_6m": 1.0,
    }
    base.update(overrides)
    return base


class TestMockScorer:
    """Unit tests for MockScorer."""

    def setup_method(self):
        self.scorer = MockScorer()
        self.scorer.load_model("")

    def test_model_version(self):
        assert self.scorer.get_model_version() == "mock-v0.1.0"

    def test_base_value(self):
        assert self.scorer.get_base_value() == 0.304

    def test_predict_returns_tuple(self):
        result = self.scorer.predict(_make_features())
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_probability_in_range(self):
        prob, _ = self.scorer.predict(_make_features())
        assert 0.01 <= prob <= 0.99

    def test_shap_has_all_features(self):
        _, shap = self.scorer.predict(_make_features())
        for feat in FEATURE_NAMES:
            assert feat in shap, f"Missing SHAP for {feat}"

    def test_deterministic(self):
        """Identical inputs must produce identical outputs."""
        features = _make_features(age=25, past_due_30d=3)
        result1 = self.scorer.predict(features)
        result2 = self.scorer.predict(features)
        assert result1 == result2

    def test_high_risk_gives_higher_probability(self):
        """More delinquencies → higher P(default)."""
        low_risk = _make_features(past_due_30d=0, inquiries_6m=0)
        high_risk = _make_features(past_due_30d=5, inquiries_6m=8)
        prob_low, _ = self.scorer.predict(low_risk)
        prob_high, _ = self.scorer.predict(high_risk)
        assert prob_high > prob_low

    def test_income_reduces_risk(self):
        """Higher income → lower P(default)."""
        poor = _make_features(monthly_income=15_000)
        rich = _make_features(monthly_income=200_000)
        prob_poor, _ = self.scorer.predict(poor)
        prob_rich, _ = self.scorer.predict(rich)
        assert prob_rich < prob_poor

    def test_shap_sign_past_due(self):
        """past_due_30d > 0 should produce positive SHAP (pushes toward default)."""
        _, shap = self.scorer.predict(_make_features(past_due_30d=3))
        assert shap["past_due_30d"] > 0

    def test_shap_sign_income(self):
        """High income should produce negative SHAP (pushes away from default)."""
        _, shap = self.scorer.predict(_make_features(monthly_income=100_000))
        assert shap["monthly_income"] < 0
