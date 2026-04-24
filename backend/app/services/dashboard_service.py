"""
Dashboard service — recalculates business metrics for a given threshold.

Loads the full CSV dataset, scores every row through the scorer,
applies the threshold, and computes confusion matrix + KPIs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

import numpy as np
import pandas as pd

from app.ml_inference.base import AbstractScorer, FEATURE_NAMES
from app.schemas.dashboard import (
    ConfusionMetrics,
    DashboardRequest,
    DashboardResponse,
)

logger = logging.getLogger(__name__)

# Path to the dataset (relative to the backend/ working directory)
_DATA_PATH = Path("data") / "credit_scoring_dataset.csv"


# ── Metric helpers ───────────────────────────────────────────

def _roc_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Compute ROC-AUC without sklearn (same formula as baseline)."""
    y_bool = y_true.astype(bool)
    pos = scores[y_bool]
    neg = scores[~y_bool]
    if len(pos) == 0 or len(neg) == 0:
        return 0.0
    auc = (
        np.sum(pos[:, None] > neg)
        + 0.5 * np.sum(pos[:, None] == neg)
    ) / (len(pos) * len(neg))
    return float(auc)


def _pr_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Compute PR-AUC without sklearn (same formula as baseline)."""
    order = np.argsort(-scores)
    yt = y_true[order].astype(int)
    tp = np.cumsum(yt)
    fp = np.cumsum(1 - yt)
    prec = tp / np.maximum(tp + fp, 1)
    return float((prec * yt).sum() / max(int(yt.sum()), 1))


# ── Service ──────────────────────────────────────────────────

class DashboardService:
    """
    Stateless service that computes business metrics over the full dataset.
    """

    def __init__(self, scorer: AbstractScorer, data_path: Path = _DATA_PATH) -> None:
        self._scorer = scorer
        self._data_path = data_path

    def compute_metrics(self, request: DashboardRequest) -> DashboardResponse:
        """
        Score all rows in the dataset, apply *threshold*, and return KPIs.

        This is fast (~10 ms for 500 rows with MockScorer).
        """
        threshold = request.threshold

        # 1. Load dataset
        df = pd.read_csv(self._data_path)
        y_true = df["target"].to_numpy(dtype=int)

        # 2. Score every row
        probabilities = self._score_all(df)
        scores = np.array(probabilities)

        # 3. Apply threshold → binary predictions
        predictions = (scores >= threshold).astype(int)

        # 4. Confusion matrix
        tp = int(np.sum((predictions == 1) & (y_true == 1)))
        tn = int(np.sum((predictions == 0) & (y_true == 0)))
        fp = int(np.sum((predictions == 1) & (y_true == 0)))
        fn = int(np.sum((predictions == 0) & (y_true == 1)))

        # 5. Derived metrics
        total = len(y_true)
        total_defaults = int(y_true.sum())

        # Approved = predicted as non-default (prediction == 0)
        approved_mask = predictions == 0
        n_approved = int(approved_mask.sum())
        approval_rate = n_approved / total if total > 0 else 0.0

        # Default rate among approved
        defaults_in_approved = int(np.sum((y_true == 1) & approved_mask))
        default_rate_in_approved = (
            defaults_in_approved / n_approved if n_approved > 0 else 0.0
        )

        # Expected loss reduction vs. "approve everyone"
        # If we approve everyone: all defaults are losses → loss = total_defaults
        # With threshold: losses = fn (missed defaults that we approved)
        baseline_loss = total_defaults
        actual_loss = fn  # defaults we failed to catch
        loss_reduction = (
            (baseline_loss - actual_loss) / baseline_loss * 100
            if baseline_loss > 0
            else 0.0
        )

        # Classification metrics
        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )

        # ROC-AUC & PR-AUC (threshold-independent)
        roc = _roc_auc(y_true, scores)
        pr = _pr_auc(y_true, scores)

        return DashboardResponse(
            threshold=threshold,
            approval_rate=round(approval_rate, 4),
            default_rate_in_approved=round(default_rate_in_approved, 4),
            expected_loss_reduction=round(loss_reduction, 2),
            roc_auc=round(roc, 4),
            pr_auc=round(pr, 4),
            accuracy=round(accuracy, 4),
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1_score=round(f1, 4),
            confusion=ConfusionMetrics(
                true_positives=tp,
                true_negatives=tn,
                false_positives=fp,
                false_negatives=fn,
            ),
            total_applications=total,
            total_defaults=total_defaults,
        )

    def _score_all(self, df: pd.DataFrame) -> List[float]:
        """Score every row through the scorer, return list of P(default)."""
        probabilities: List[float] = []
        for _, row in df.iterrows():
            features = {feat: float(row[feat]) for feat in FEATURE_NAMES}
            prob, _ = self._scorer.predict(features)
            probabilities.append(prob)
        return probabilities
