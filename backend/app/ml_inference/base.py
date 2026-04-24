"""
Abstract base class for all scoring models.

CONTRACT FOR DATA SCIENTIST:
    1. Inherit from AbstractScorer
    2. Implement all four abstract methods
    3. Place your trained model file in  ml_inference/models/
    4. Everything else (API, validation, routing) is handled by the backend
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple


# The 8 features expected by the model, in the order used during training.
FEATURE_NAMES: list[str] = [
    "age",
    "monthly_income",
    "employment_years",
    "loan_amount",
    "loan_term_months",
    "interest_rate",
    "past_due_30d",
    "inquiries_6m",
]


class AbstractScorer(ABC):
    """
    Interface that every scorer must implement.

    The backend calls these methods — the concrete implementation
    decides whether to use a pickle, ONNX, TF-Lite, or an API call.
    """

    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """
        Load a trained model from *model_path*.

        Called once at application startup.  The implementation should
        store whatever is needed (weights, scaler params, etc.) as
        instance attributes.
        """
        ...

    @abstractmethod
    def predict(self, features: Dict[str, float]) -> Tuple[float, Dict[str, float]]:
        """
        Score a single loan application.

        Args:
            features: mapping ``{feature_name: value}`` with exactly
                      the 8 keys listed in ``FEATURE_NAMES``.

        Returns:
            A tuple ``(probability_of_default, shap_values)`` where
            *probability_of_default* ∈ [0, 1] and *shap_values* is a
            dict ``{feature_name: contribution}`` (positive = pushes
            toward default, negative = pushes toward non-default).
        """
        ...

    @abstractmethod
    def get_base_value(self) -> float:
        """
        Return the SHAP base value (mean P(default) on the training set).

        Used as the starting point for waterfall / force-plot charts.
        """
        ...

    @abstractmethod
    def get_model_version(self) -> str:
        """
        Return a human-readable model version string.

        Included in every API response so the frontend can display it.
        """
        ...
