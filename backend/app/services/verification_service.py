"""Verification Service Wrapper."""

from typing import Dict, Any, Optional
import numpy as np

from outgraph.ml.verification.physics_engine import PhysicsVerificationEngine, PhysicsEvidenceProfile
from outgraph.ml.matchers.base import MatchResult


class VerificationService:
    """Service layer interface for physics verification."""

    def __init__(self):
        self.engine = PhysicsVerificationEngine()

    def verify(
        self,
        src_img: np.ndarray,
        tgt_img: np.ndarray,
        src_meta: Dict[str, Any],
        tgt_meta: Dict[str, Any],
        match_result: MatchResult,
        src_dem: Optional[np.ndarray] = None,
        tgt_dem: Optional[np.ndarray] = None,
    ) -> PhysicsEvidenceProfile:
        return self.engine.verify_correspondence(
            src_image=src_img,
            tgt_image=tgt_img,
            src_meta=src_meta,
            tgt_meta=tgt_meta,
            match_result=match_result,
            src_dem=src_dem,
            tgt_dem=tgt_dem,
        )
