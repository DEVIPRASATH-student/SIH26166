"""Uncertainty Service Wrapper."""

from outgraph.ml.uncertainty.uncertainty_engine import UncertaintyEngine, UncertaintyBreakdown
from outgraph.ml.verification.physics_engine import PhysicsEvidenceProfile


class UncertaintyService:
    """Service layer interface for uncertainty estimation."""

    def __init__(self):
        self.engine = UncertaintyEngine()

    def compute_uncertainty(self, profile: PhysicsEvidenceProfile) -> UncertaintyBreakdown:
        return self.engine.compute_correspondence_uncertainty(profile)
