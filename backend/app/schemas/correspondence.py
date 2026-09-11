"""Correspondence Pydantic Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CorrespondenceAnalyzeRequest(BaseModel):
    source_observation_id: str
    target_observation_id: str
    matcher_algorithm: str = Field("SIFT", description="SIFT, ORB, SuperPoint-Adapter, LoFTR-Adapter, RIFT-Adapter")
    ratio_threshold: float = Field(0.80, ge=0.5, le=0.95)


class MatchPoint(BaseModel):
    src_x: float
    src_y: float
    tgt_x: float
    tgt_y: float
    is_inlier: bool
    distance: float


class CorrespondenceResponse(BaseModel):
    id: str
    source_observation_id: str
    target_observation_id: str
    matcher_algorithm: str
    num_candidate_matches: int
    num_inliers: int
    inlier_ratio: float
    visual_confidence: float
    overall_confidence: float
    status: str  # VERIFIED, UNCERTAIN, REJECTED
    matches: List[MatchPoint]
    evidence_profile: Optional[Dict[str, Any]] = None
    uncertainty_breakdown: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
