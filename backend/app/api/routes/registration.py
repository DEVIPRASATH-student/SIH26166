"""Registration API Endpoints."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.correspondence_service import CorrespondenceService
from ...services.registration_service import RegistrationService
from ...services.observation_service import ObservationService
from ...schemas.evidence import RegistrationRequest, RegistrationResponse
from ...models.evidence import RegistrationExperimentModel
from outgraph.ml.matchers.adapters import get_matcher

router = APIRouter(prefix="/registration", tags=["Registration"])


@router.post("/run", response_model=RegistrationResponse)
def run_subpixel_registration(request: RegistrationRequest, db: Session = Depends(get_db)):
    """Runs coarse-to-fine sub-pixel registration and generates difference overlay."""
    corr_service = CorrespondenceService(db)
    reg_service = RegistrationService(db)
    obs_service = ObservationService(db)

    corr = corr_service.get_correspondence(request.correspondence_id)
    if not corr:
        raise HTTPException(status_code=404, detail=f"Correspondence {request.correspondence_id} not found")

    src_img = obs_service.load_image_from_disk(corr.source_observation_id)
    tgt_img = obs_service.load_image_from_disk(corr.target_observation_id)

    if src_img is None or tgt_img is None:
        raise HTTPException(status_code=400, detail="Images not found on disk")

    matcher = get_matcher(corr.matcher_algorithm)
    match_res = matcher.match(src_img, tgt_img)

    exp = reg_service.run_registration(
        correspondence_id=corr.id,
        src_img=src_img,
        tgt_img=tgt_img,
        match_result=match_res,
        apply_subpixel_ecc=request.apply_subpixel_ecc,
    )

    H = json.loads(exp.transformation_matrix_json) if exp.transformation_matrix_json else []

    return RegistrationResponse(
        id=exp.id,
        correspondence_id=exp.correspondence_id,
        is_success=exp.is_success,
        transformation_matrix=H,
        registered_image_url=exp.registered_image_path,
        difference_image_url=exp.difference_image_path,
        rmse=exp.rmse,
        subpixel_error_px=exp.subpixel_error_px,
        inlier_ratio=exp.inlier_ratio,
        spatial_coverage=exp.spatial_coverage,
        algorithm=exp.algorithm,
        metadata=json.loads(exp.metadata_json) if exp.metadata_json else {},
        created_at=exp.created_at,
    )


@router.get("/{correspondence_id}", response_model=RegistrationResponse)
def get_registration(correspondence_id: str, db: Session = Depends(get_db)):
    """Retrieves existing registration experiment for a correspondence."""
    reg_service = RegistrationService(db)
    exp = reg_service.get_registration_by_correspondence(correspondence_id)
    if not exp:
        raise HTTPException(status_code=404, detail=f"Registration for {correspondence_id} not found")

    H = json.loads(exp.transformation_matrix_json) if exp.transformation_matrix_json else []

    return RegistrationResponse(
        id=exp.id,
        correspondence_id=exp.correspondence_id,
        is_success=exp.is_success,
        transformation_matrix=H,
        registered_image_url=exp.registered_image_path,
        difference_image_url=exp.difference_image_path,
        rmse=exp.rmse,
        subpixel_error_px=exp.subpixel_error_px,
        inlier_ratio=exp.inlier_ratio,
        spatial_coverage=exp.spatial_coverage,
        algorithm=exp.algorithm,
        metadata=json.loads(exp.metadata_json) if exp.metadata_json else {},
        created_at=exp.created_at,
    )
