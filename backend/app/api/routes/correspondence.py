"""Correspondence API Endpoints."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.correspondence_service import CorrespondenceService
from ...schemas.correspondence import CorrespondenceAnalyzeRequest, CorrespondenceResponse, MatchPoint
from ...schemas.evidence import EvidenceProfileResponse
from ...models.correspondence import CorrespondenceModel
from ...models.evidence import CorrespondenceEvidenceModel

router = APIRouter(prefix="/correspondence", tags=["Correspondence"])


@router.post("/analyze", response_model=CorrespondenceResponse)
def analyze_correspondence(
    request: CorrespondenceAnalyzeRequest, db: Session = Depends(get_db)
):
    """Executes feature extraction, matching, and multi-pillar physics verification."""
    corr_service = CorrespondenceService(db)
    try:
        corr, ev, match_res = corr_service.analyze_correspondence(
            src_obs_id=request.source_observation_id,
            tgt_obs_id=request.target_observation_id,
            matcher_name=request.matcher_algorithm,
            ratio_threshold=request.ratio_threshold,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    raw_matches = json.loads(corr.matches_data_json) if corr.matches_data_json else []
    match_objs = [MatchPoint(**m) for m in raw_matches]

    evidence_dict = {
        "visual_score": ev.visual_score,
        "geometry_score": ev.geometry_score,
        "illumination_score": ev.illumination_score,
        "terrain_score": ev.terrain_score,
        "scale_score": ev.scale_score,
        "spatial_score": ev.spatial_score,
        "overall_confidence": corr.overall_confidence,
        "status": corr.status,
        "rejection_reasons": json.loads(ev.rejection_reasons_json) if ev.rejection_reasons_json else [],
    }

    unc_dict = {
        "total_uncertainty": ev.total_uncertainty,
        "evidence_disagreement": ev.evidence_disagreement,
        "geometric_instability": ev.geometric_instability,
        "feature_ambiguity": ev.feature_ambiguity,
        "spatial_sparsity": ev.spatial_sparsity,
        "calibration_status": ev.calibration_status,
    }

    return CorrespondenceResponse(
        id=corr.id,
        source_observation_id=corr.source_observation_id,
        target_observation_id=corr.target_observation_id,
        matcher_algorithm=corr.matcher_algorithm,
        num_candidate_matches=corr.num_candidate_matches,
        num_inliers=corr.num_inliers,
        inlier_ratio=corr.inlier_ratio,
        visual_confidence=corr.visual_confidence,
        overall_confidence=corr.overall_confidence,
        status=corr.status,
        matches=match_objs,
        evidence_profile=evidence_dict,
        uncertainty_breakdown=unc_dict,
        created_at=corr.created_at,
    )


@router.get("", response_model=List[CorrespondenceResponse])
def list_correspondences(db: Session = Depends(get_db)):
    """Lists all evaluated correspondence tasks."""
    corr_service = CorrespondenceService(db)
    corrs = corr_service.list_correspondences()
    result = []
    for corr in corrs:
        ev = corr_service.get_evidence(corr.id)
        raw_matches = json.loads(corr.matches_data_json) if corr.matches_data_json else []
        match_objs = [MatchPoint(**m) for m in raw_matches]

        evidence_dict = None
        unc_dict = None
        if ev:
            evidence_dict = {
                "visual_score": ev.visual_score,
                "geometry_score": ev.geometry_score,
                "illumination_score": ev.illumination_score,
                "terrain_score": ev.terrain_score,
                "scale_score": ev.scale_score,
                "spatial_score": ev.spatial_score,
                "overall_confidence": corr.overall_confidence,
                "status": corr.status,
                "rejection_reasons": json.loads(ev.rejection_reasons_json) if ev.rejection_reasons_json else [],
            }
            unc_dict = {
                "total_uncertainty": ev.total_uncertainty,
                "evidence_disagreement": ev.evidence_disagreement,
                "geometric_instability": ev.geometric_instability,
                "feature_ambiguity": ev.feature_ambiguity,
                "spatial_sparsity": ev.spatial_sparsity,
                "calibration_status": ev.calibration_status,
            }

        result.append(
            CorrespondenceResponse(
                id=corr.id,
                source_observation_id=corr.source_observation_id,
                target_observation_id=corr.target_observation_id,
                matcher_algorithm=corr.matcher_algorithm,
                num_candidate_matches=corr.num_candidate_matches,
                num_inliers=corr.num_inliers,
                inlier_ratio=corr.inlier_ratio,
                visual_confidence=corr.visual_confidence,
                overall_confidence=corr.overall_confidence,
                status=corr.status,
                matches=match_objs,
                evidence_profile=evidence_dict,
                uncertainty_breakdown=unc_dict,
                created_at=corr.created_at,
            )
        )
    return result


@router.get("/{correspondence_id}", response_model=CorrespondenceResponse)
def get_correspondence_by_id(correspondence_id: str, db: Session = Depends(get_db)):
    """Retrieves a single correspondence by ID."""
    corr_service = CorrespondenceService(db)
    corr = corr_service.get_correspondence(correspondence_id)
    if not corr:
        raise HTTPException(status_code=404, detail=f"Correspondence {correspondence_id} not found")

    ev = corr_service.get_evidence(corr.id)
    raw_matches = json.loads(corr.matches_data_json) if corr.matches_data_json else []
    match_objs = [MatchPoint(**m) for m in raw_matches]

    evidence_dict = None
    unc_dict = None
    if ev:
        evidence_dict = {
            "visual_score": ev.visual_score,
            "geometry_score": ev.geometry_score,
            "illumination_score": ev.illumination_score,
            "terrain_score": ev.terrain_score,
            "scale_score": ev.scale_score,
            "spatial_score": ev.spatial_score,
            "overall_confidence": corr.overall_confidence,
            "status": corr.status,
            "rejection_reasons": json.loads(ev.rejection_reasons_json) if ev.rejection_reasons_json else [],
        }
        unc_dict = {
            "total_uncertainty": ev.total_uncertainty,
            "evidence_disagreement": ev.evidence_disagreement,
            "geometric_instability": ev.geometric_instability,
            "feature_ambiguity": ev.feature_ambiguity,
            "spatial_sparsity": ev.spatial_sparsity,
            "calibration_status": ev.calibration_status,
        }

    return CorrespondenceResponse(
        id=corr.id,
        source_observation_id=corr.source_observation_id,
        target_observation_id=corr.target_observation_id,
        matcher_algorithm=corr.matcher_algorithm,
        num_candidate_matches=corr.num_candidate_matches,
        num_inliers=corr.num_inliers,
        inlier_ratio=corr.inlier_ratio,
        visual_confidence=corr.visual_confidence,
        overall_confidence=corr.overall_confidence,
        status=corr.status,
        matches=match_objs,
        evidence_profile=evidence_dict,
        uncertainty_breakdown=unc_dict,
        created_at=corr.created_at,
    )
