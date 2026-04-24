"""
ml_inference package — isolated ML scoring module.

Public API:
    AbstractScorer  — base interface (ABC) for all scorers
    MockScorer      — deterministic mock for frontend development
    RealScorer      — placeholder for the real model (Data Scientist fills in)
"""

from .base import AbstractScorer
from .mock_scorer import MockScorer
from .real_scorer import RealScorer

__all__ = ["AbstractScorer", "MockScorer", "RealScorer"]
