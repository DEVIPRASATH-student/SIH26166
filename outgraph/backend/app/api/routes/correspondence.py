"""Correspondence API Endpoints."""

import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.correspondence_service import CorrespondenceService
from ...services.observation_service import ObservationService
from ...services.pipeline_service import PipelineController
from ...schemas.correspondence import CorrespondenceAnalyzeRequest, CorrespondenceResponse, MatchPoint
from ...models.correspondence import CorrespondenceModel
from ...models.evidence import CorrespondenceEvidenceModel

router = APIRouter(prefix="/correspondence", tags=["Correspondence"])


def _extract_gate_results(rejection_reasons: List[str]) -> Dict[str, Any]:
    reasons_str = " ".join(rejection_reasons)
    return {
        "GATE1": {
            "gate_id": "GATE1",
            "gate_name": "INVALID_SOURCE_GROUNDGRID",
            "status": "REJECTED" if "GATE1_INVALID_SOURCE_GROUNDGRID" in reasons_str else "PASS",
            "reason": "Calibrated pushbroom source grid verification",
        },
        "GATE2": {
            "gate_id": "GATE2",
            "gate_name": "DEM_OUT_OF_BOUNDS_OR_NODATA",
            "status": "REJECTED" if "GATE2_DEM_OUT_OF_BOUNDS_OR_NODATA" in reasons_str else "PASS",
            "reason": "SLDEM2015 elevation corridor coverage",
        },
        "GATE3": {
            "gate_id": "GATE3",
            "gate_name": "TARGET_OUTSIDE_CALIBRATED_SWATH",
            "status": "REJECTED" if "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH" in reasons_str else "PASS",
            "reason": "Sensor footprint spatial overlap and swath verification",
        },
        "GATE4": {
            "gate_id": "GATE4",
            "gate_name": "TARGET_CLAMPED_TO_SWATH_BOUNDARY",
            "status": "REJECTED" if "GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY" in reasons_str else "PASS",
            "reason": "Boundary clamping detector",
        },
        "GATE5": {
            "gate_id": "GATE5",
            "gate_name": "TARGET_OUTSIDE_ELEVATION_CORRIDOR",
            "status": "REJECTED" if "GATE5_TARGET_OUTSIDE_ELEVATION_CORRIDOR" in reasons_str else "PASS",
            "reason": "DEM elevation corridor parallax bounds",
        },
        "GATE6": {
            "gate_id": "GATE6",
            "gate_name": "BIDIRECTIONAL_RESIDUAL_TOO_LARGE",
            "status": "REJECTED" if "GATE6_BIDIRECTIONAL_RESIDUAL_TOO_LARGE" in reasons_str else "PASS",
            "reason": "Ray-casting bidirectional consistency residual",
        },
    }


def _build_response_from_models(
    corr: CorrespondenceModel,
    ev: Optional[CorrespondenceEvidenceModel],
    pipeline_res: Optional[Any] = None,
) -> CorrespondenceResponse:
    raw_matches = json.loads(corr.matches_data_json) if corr.matches_data_json else []
    match_objs = [MatchPoint(**m) for m in raw_matches]

    rejection_reasons = []
    evidence_dict = None
    unc_dict = None

    if ev:
        rejection_reasons = json.loads(ev.rejection_reasons_json) if ev.rejection_reasons_json else []
        evidence_dict = {
            "visual_score": ev.visual_score,
            "geometry_score": ev.geometry_score,
            "illumination_score": ev.illumination_score,
            "terrain_score": ev.terrain_score,
            "scale_score": ev.scale_score,
            "spatial_score": ev.spatial_score,
            "overall_confidence": corr.overall_confidence,
            "status": corr.status,
            "rejection_reasons": rejection_reasons,
        }
        unc_dict = {
            "total_uncertainty": ev.total_uncertainty,
            "evidence_disagreement": ev.evidence_disagreement,
            "geometric_instability": ev.geometric_instability,
            "feature_ambiguity": ev.feature_ambiguity,
            "spatial_sparsity": ev.spatial_sparsity,
            "calibration_status": ev.calibration_status,
            "saturation_limit": ">4 px uncertainty saturation limit preserved",
        }

    gate_results = _extract_gate_results(rejection_reasons)
    phys_passed = (corr.status not in ["REJECTED", "GEOMETRICALLY_DEGENERATE"]) and (corr.num_inliers > 0)
    geom_status = "VERIFIED" if corr.num_inliers >= 4 else "DEGENERATE"
    phys_status = "PASS" if phys_passed else "REJECTED"

    is_synth = bool(corr.is_synthetic)
    data_prov = {
        "type": "SYNTHETIC" if is_synth else "REAL_LUNAR",
        "is_synthetic": is_synth,
    }

    limitations = [
        "PHYSICAL CORRESPONDENCE NOT VALIDATED" if not is_synth else "SYNTHETIC CONTROLLED SCENARIO ONLY",
        "REAL-DATA ACCURACY = N/A",
        "REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED",
        "UNKNOWN != NEGATIVE",
        "ENTITY ASSOCIATION != DIRECT IMAGE CORRESPONDENCE",
    ]

    explanation = None
    k_gaps = []
    recs = []
    wm_effect = None

    if pipeline_res is not None:
        explanation = dict(pipeline_res.explanation_card)
        explanation["decision"] = pipeline_res.status
        k_gaps = pipeline_res.knowledge_gaps
        recs = [pipeline_res.recommendation] if pipeline_res.recommendation else []
        wm_effect = {"entity_id": pipeline_res.entity_id, "entity_state": pipeline_res.entity_state}
        limitations = pipeline_res.scientific_limitations
    else:
        explanation = {
            "decision": corr.status,

            "primary_reason": "Physical swath boundary separation" if "GATE3" in str(rejection_reasons) else "Multi-pillar verification",
            "failed_gate": "GATE3" if "GATE3" in str(rejection_reasons) else None,
            "rejection_reasons": rejection_reasons,
            "limitations": limitations,
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
        is_synthetic=corr.is_synthetic,
        matches=match_objs,
        evidence_profile=evidence_dict,
        uncertainty_breakdown=unc_dict,
        created_at=corr.created_at,
        candidate_count=corr.num_candidate_matches,
        inlier_count=corr.num_inliers,
        matcher=corr.matcher_algorithm,
        geometric_status=geom_status,
        physical_verification_status=phys_status,
        physical_gate_results=gate_results,
        rejection_reasons=rejection_reasons,
        uncertainty=unc_dict,
        world_model_effect=wm_effect,
        knowledge_gaps=k_gaps,
        recommendations=recs,
        explanation=explanation,
        provenance=data_prov,
        data_provenance=data_prov,
        limitations=limitations,
        scientific_limitations=limitations,
        observation={
            "source_observation_id": corr.source_observation_id,
            "target_observation_id": corr.target_observation_id,
            "is_synthetic": is_synth,
        },
        correspondence={
            "id": corr.id,
            "num_candidate_matches": corr.num_candidate_matches,
            "num_inliers": corr.num_inliers,
            "inlier_ratio": corr.inlier_ratio,
            "status": corr.status,
        },
        geometric_verification={
            "status": geom_status,
            "num_inliers": corr.num_inliers,
            "inlier_ratio": corr.inlier_ratio,
        },
        physical_verification={
            "passed": phys_passed,
            "status": phys_status,
            "rejection_reasons": rejection_reasons,
            "gates": gate_results,
        },
        evidence=evidence_dict,
        world_model=wm_effect,
    )


@router.post("/analyze", response_model=CorrespondenceResponse)
def analyze_correspondence(
    request: CorrespondenceAnalyzeRequest, db: Session = Depends(get_db)
):
    """Executes feature extraction, matching, and multi-pillar physics verification via PipelineController."""
    # CRITICAL RULE 13 & 14: Physical verification MUST NOT be bypassable through the API
    if request.force_accept is not None and request.force_accept is True:
        raise HTTPException(
            status_code=400,
            detail="Physical verification bypass is strictly forbidden by scientific safety rules (Rule 13, 14)",
        )

    # Validate observation existence
    obs_service = ObservationService(db)
    src_obs = obs_service.get_observation(request.source_observation_id)
    tgt_obs = obs_service.get_observation(request.target_observation_id)

    if not src_obs:
        raise HTTPException(
            status_code=404,
            detail=f"Source observation '{request.source_observation_id}' not found",
        )
    if not tgt_obs:
        raise HTTPException(
            status_code=404,
            detail=f"Target observation '{request.target_observation_id}' not found",
        )

    # Validate matcher
    allowed_matchers = ["SIFT", "ORB", "SuperPoint-Adapter", "LoFTR-Adapter", "RIFT-Adapter"]
    if request.matcher_algorithm not in allowed_matchers:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported matcher algorithm: '{request.matcher_algorithm}'. Must be one of: {allowed_matchers}",
        )

    # Execute full Phase 8.1 Integrated Scientific Pipeline
    pipeline_controller = PipelineController(db)
    try:
        pipeline_res = pipeline_controller.execute_pipeline(
            src_obs_id=request.source_observation_id,
            tgt_obs_id=request.target_observation_id,
            matcher_name=request.matcher_algorithm,
            ratio_threshold=request.ratio_threshold,
            scientific_question=request.scientific_question or "spectral analysis",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failure: {str(e)}")

    corr_service = CorrespondenceService(db)
    corr_id = f"CORR-{request.source_observation_id}-{request.target_observation_id}"
    corr = corr_service.get_correspondence(corr_id)
    if not corr:
        raise HTTPException(status_code=500, detail=f"Correspondence record {corr_id} was not persisted")

    # Update corr.status to match pipeline_res.status for full consistency
    corr.status = pipeline_res.status
    db.commit()
    db.refresh(corr)

    ev = corr_service.get_evidence(corr.id)
    return _build_response_from_models(corr, ev, pipeline_res)


@router.get("", response_model=List[CorrespondenceResponse])
def list_correspondences(db: Session = Depends(get_db)):
    """Lists all evaluated correspondence tasks."""
    corr_service = CorrespondenceService(db)
    corrs = corr_service.list_correspondences()
    result = []
    for corr in corrs:
        ev = corr_service.get_evidence(corr.id)
        result.append(_build_response_from_models(corr, ev))
    return result


@router.get("/{correspondence_id}", response_model=CorrespondenceResponse)
def get_correspondence_by_id(correspondence_id: str, db: Session = Depends(get_db)):
    """Retrieves a single correspondence by ID."""
    corr_service = CorrespondenceService(db)
    corr = corr_service.get_correspondence(correspondence_id)
    if not corr:
        raise HTTPException(status_code=404, detail=f"Correspondence {correspondence_id} not found")

    ev = corr_service.get_evidence(corr.id)
    return _build_response_from_models(corr, ev)
