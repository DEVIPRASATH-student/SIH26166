"""Correspondence Pydantic Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class CorrespondenceAnalyzeRequest(BaseModel):
    source_observation_id: str
    target_observation_id: str
    matcher_algorithm: str = Field("SIFT", description="SIFT, ORB, SuperPoint-Adapter, LoFTR-Adapter, RIFT-Adapter")
    ratio_threshold: float = Field(0.80, ge=0.5, le=0.95)
    scientific_question: Optional[str] = Field("spectral analysis", description="fine morphology, terrain analysis, elevation analysis, spectral analysis")
    force_accept: Optional[bool] = Field(None, description="Forbidden bypass parameter")


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
    status: str  # ACCEPTED, VERIFIED, UNCERTAIN, REJECTED, UNKNOWN, CONTRADICTED
    is_synthetic: bool = True
    matches: List[MatchPoint]
    evidence_profile: Optional[Dict[str, Any]] = None
    uncertainty_breakdown: Optional[Dict[str, Any]] = None
    created_at: datetime

    # Phase 8.2 Top-Level Scientific Contract Fields
    candidate_count: Optional[int] = None
    inlier_count: Optional[int] = None
    matcher: Optional[str] = None
    geometric_status: Optional[str] = None
    physical_verification_status: Optional[str] = None
    physical_gate_results: Optional[Dict[str, Any]] = None
    rejection_reasons: Optional[List[str]] = None
    uncertainty: Optional[Dict[str, Any]] = None
    world_model_effect: Optional[Dict[str, Any]] = None
    knowledge_gaps: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    explanation: Optional[Dict[str, Any]] = None
    provenance: Optional[Dict[str, Any]] = None
    data_provenance: Optional[Dict[str, Any]] = None
    limitations: Optional[List[str]] = None
    scientific_limitations: Optional[List[str]] = None

    # Grouped Domain Contract Fields
    observation: Optional[Dict[str, Any]] = None
    correspondence: Optional[Dict[str, Any]] = None
    geometric_verification: Optional[Dict[str, Any]] = None
    physical_verification: Optional[Dict[str, Any]] = None
    evidence: Optional[Dict[str, Any]] = None
    world_model: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

