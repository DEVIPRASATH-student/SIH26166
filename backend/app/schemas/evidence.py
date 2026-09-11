"""Evidence and Registration Pydantic Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class EvidenceProfileResponse(BaseModel):
    correspondence_id: str
    visual_score: float
    geometry_score: float
    illumination_score: float
    terrain_score: float
    scale_score: float
    spatial_score: float
    overall_confidence: float
    status: str
    total_uncertainty: float
    evidence_disagreement: float
    geometric_instability: float
    feature_ambiguity: float
    spatial_sparsity: float
    calibration_status: str
    mean_reprojection_error_px: float
    condition_number: float
    rejection_reasons: List[str]


class RegistrationRequest(BaseModel):
    correspondence_id: str
    apply_subpixel_ecc: bool = True


class RegistrationResponse(BaseModel):
    id: str
    correspondence_id: str
    is_success: bool
    transformation_matrix: List[List[float]]
    registered_image_url: str
    difference_image_url: str
    rmse: float
    subpixel_error_px: float
    inlier_ratio: float
    spatial_coverage: float
    algorithm: str
    metadata: Dict[str, Any]
    created_at: datetime
