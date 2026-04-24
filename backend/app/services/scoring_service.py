"""
Scoring service — orchestrates the flow:

    ScoringRequest  →  validate  →  scorer.predict()  →  enrich  →  ScoringResponse

This layer is pure business logic: no HTTP, no framework dependencies.
"""

from __future__ import annotations

from app.ml_inference.base import AbstractScorer
from app.schemas.scoring import (
    RiskSegment,
    ScoringRequest,
    ScoringResponse,
    ShapValues,
)


# ── Risk segment thresholds ──────────────────────────────────

_RISK_SEGMENTS = [
    # (max_probability, label, hex_color, description)
    (0.20, "low",      "#22C55E", "Низкий риск — надёжный заёмщик"),
    (0.45, "medium",   "#F59E0B", "Средний риск — требует внимания"),
    (0.70, "high",     "#EF4444", "Высокий риск — значительная вероятность дефолта"),
    (1.00, "critical", "#991B1B", "Критический риск — крайне высокая вероятность дефолта"),
]


def _classify_risk(probability: float) -> RiskSegment:
    """Map a probability to a risk segment."""
    for max_p, label, color, desc in _RISK_SEGMENTS:
        if probability <= max_p:
            return RiskSegment(label=label, color=color, description=desc)
    # fallback (should never happen)
    return RiskSegment(label="critical", color="#991B1B", description="Критический риск")


def _probability_to_credit_score(probability: float) -> int:
    """
    Convert P(default) ∈ [0, 1] to a FICO-like score ∈ [300, 850].

    Mapping:  P=0 → 850,  P=1 → 300  (linear inverse).
    """
    score = int(850 - (850 - 300) * probability)
    return max(300, min(850, score))


# ── Service ──────────────────────────────────────────────────

class ScoringService:
    """
    Stateless service that wraps the ML scorer and produces
    a fully enriched ScoringResponse.
    """

    def __init__(self, scorer: AbstractScorer) -> None:
        self._scorer = scorer

    def score(
        self,
        request: ScoringRequest,
        threshold: float = 0.5,
    ) -> ScoringResponse:
        """
        Run scoring pipeline on a single loan application.

        Args:
            request:   Validated applicant data.
            threshold: Decision cutoff — P(default) >= threshold → DECLINED.

        Returns:
            Fully populated ScoringResponse with XAI data.
        """
        features = request.to_feature_dict()

        # 1. ML inference
        probability, shap_dict = self._scorer.predict(features)

        # 2. Binary decision
        decision = "DECLINED" if probability >= threshold else "APPROVED"

        # 3. Credit score (FICO-like)
        credit_score = _probability_to_credit_score(probability)

        # 4. Risk segment
        risk_segment = _classify_risk(probability)

        # 5. SHAP wrapper
        shap_values = ShapValues(
            base_value=self._scorer.get_base_value(),
            feature_contributions=shap_dict,
        )

        return ScoringResponse(
            decision=decision,
            probability_of_default=round(probability, 4),
            credit_score=credit_score,
            risk_segment=risk_segment,
            shap_values=shap_values,
            model_version=self._scorer.get_model_version(),
            threshold_used=threshold,
        )
