"""Registration Service Wrapper."""

import json
from typing import Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
import numpy as np
import cv2

from ..core.config import settings
from ..models.evidence import RegistrationExperimentModel
from ..models.correspondence import CorrespondenceModel
from outgraph.ml.registration.subpixel_engine import SubPixelRegistrationEngine, RegistrationExperimentResult
from outgraph.ml.matchers.base import MatchResult


class RegistrationService:
    """Handles coarse-to-fine registration and persistent visual diff rendering."""

    def __init__(self, db: Session):
        self.db = db
        self.engine = SubPixelRegistrationEngine()

    def run_registration(
        self,
        correspondence_id: str,
        src_img: np.ndarray,
        tgt_img: np.ndarray,
        match_result: MatchResult,
        apply_subpixel_ecc: bool = True,
    ) -> RegistrationExperimentModel:
        """Executes registration and stores artifact overlays on disk and experiment in DB."""
        reg_res = self.engine.register(
            source_image=src_img,
            target_image=tgt_img,
            match_result=match_result,
            apply_subpixel_ecc=apply_subpixel_ecc,
        )

        reg_img_name = f"reg_{correspondence_id}.png"
        diff_img_name = f"diff_{correspondence_id}.png"

        reg_path = settings.IMAGES_DIR / reg_img_name
        diff_path = settings.IMAGES_DIR / diff_img_name

        # Save warped registered image
        if reg_res.registered_image.ndim == 3 and reg_res.registered_image.shape[2] == 3:
            cv2.imwrite(str(reg_path), cv2.cvtColor(reg_res.registered_image, cv2.COLOR_RGB2BGR))
        else:
            cv2.imwrite(str(reg_path), reg_res.registered_image)

        # Save difference overlay
        cv2.imwrite(str(diff_path), reg_res.difference_image)

        exp_id = f"REG-EXP-{correspondence_id[:8]}"
        existing = self.db.query(RegistrationExperimentModel).filter(
            RegistrationExperimentModel.correspondence_id == correspondence_id
        ).first()

        H_list = reg_res.transformation_matrix.tolist()

        if existing:
            existing.is_success = reg_res.is_success
            existing.transformation_matrix_json = json.dumps(H_list)
            existing.registered_image_path = f"/api/observations/experiments/{reg_img_name}"
            existing.difference_image_path = f"/api/observations/experiments/{diff_img_name}"
            existing.rmse = reg_res.rmse
            existing.subpixel_error_px = reg_res.estimated_subpixel_error_px
            existing.inlier_ratio = reg_res.inlier_ratio
            existing.spatial_coverage = reg_res.spatial_coverage
            existing.metadata_json = json.dumps(reg_res.metadata)
            self.db.commit()
            self.db.refresh(existing)
            return existing

        exp = RegistrationExperimentModel(
            id=exp_id,
            correspondence_id=correspondence_id,
            is_success=reg_res.is_success,
            transformation_matrix_json = json.dumps(H_list),
            registered_image_path=f"/api/observations/experiments/{reg_img_name}",
            difference_image_path=f"/api/observations/experiments/{diff_img_name}",
            rmse=reg_res.rmse,
            subpixel_error_px=reg_res.estimated_subpixel_error_px,
            inlier_ratio=reg_res.inlier_ratio,
            spatial_coverage=reg_res.spatial_coverage,
            algorithm=match_result.algorithm_name,
            metadata_json=json.dumps(reg_res.metadata),
        )
        self.db.add(exp)
        self.db.commit()
        self.db.refresh(exp)
        return exp

    def get_registration_by_correspondence(self, correspondence_id: str) -> Optional[RegistrationExperimentModel]:
        return self.db.query(RegistrationExperimentModel).filter(
            RegistrationExperimentModel.correspondence_id == correspondence_id
        ).first()
