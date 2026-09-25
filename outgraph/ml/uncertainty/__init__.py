"""Uncertainty Quantification Module.
Provides principled epistemic and aleatoric uncertainty estimation based on evidence variance,
residual reprojection divergence, and geometric condition stability.
"""
from .uncertainty_engine import UncertaintyEngine, UncertaintyBreakdown

__all__ = ["UncertaintyEngine", "UncertaintyBreakdown"]
