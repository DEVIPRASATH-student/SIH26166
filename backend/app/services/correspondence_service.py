"""Correspondence Service for Multi-Modal Observation Matching."""

import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session
import numpy as np

from ..models.observation import ObservationModel
from ..models.correspondence import CorrespondenceModel
from ..models.evidence import CorrespondenceEvidenceModel
from ..services.observation_service import ObservationService
from ..services.verification_service import VerificationService
from ..services.uncertainty_service import UncertaintyService
from outgraph.ml.matchers.adapters import get_matcher
from outgraph.ml.matchers.base import MatchResult


class CorrespondenceService:
    """Orchestrates feature extraction, cross-modal matching, physics verification, and uncertainty estimation."""

    def __init__(self, db: Session):
        self.db = db
        self.obs_service = ObservationService(db)
        self.verif_service = VerificationService()
        self.unc_service = UncertaintyService()

    def analyze_correspondence(
        self,
        src_obs_id: str,
        tgt_obs_id: str,
        matcher_name: str = "SIFT",
        ratio_threshold: float = 0.80,
    ) -> Tuple[CorrespondenceModel, CorrespondenceEvidenceModel, MatchResult]:
        """Runs the complete matching and physics verification pipeline."""
        src_obs = self.obs_service.get_observation(src_obs_id)
        tgt_obs = self.obs_service.get_observation(tgt_obs_id)

        if not src_obs or not tgt_obs:
            raise ValueError(f"Observation not found: {src_obs_id} or {tgt_obs_id}")

        src_img = self.obs_service.load_image_from_disk(src_obs_id)
        tgt_img = self.obs_service.load_image_from_disk(tgt_obs_id)

        if src_img is None or tgt_img is None:
            raise ValueError("Unable to read observation image pixels from disk.")

        # 1. Feature Matching
        matcher = get_matcher(matcher_name)
        match_res = matcher.match(src_img, tgt_img, ratio_threshold=ratio_threshold)

        # 2. Extract Metadata for Physics Engine
        src_meta = {
            "spatial_resolution_m": src_obs.spatial_resolution_m,
            "sun_azimuth_deg": src_obs.sun_azimuth_deg,
            "sun_elevation_deg": src_obs.sun_elevation_deg,
            "phase_angle_deg": src_obs.phase_angle_deg,
        }
        tgt_meta = {
            "spatial_resolution_m": tgt_obs.spatial_resolution_m,
            "sun_azimuth_deg": tgt_obs.sun_azimuth_deg,
            "sun_elevation_deg": tgt_obs.sun_elevation_deg,
            "phase_angle_deg": tgt_obs.phase_angle_deg,
        }

        # 3. Physics-based Multi-Pillar Verification
        evidence_profile = self.verif_service.verify(
            src_img=src_img,
            tgt_img=tgt_img,
            src_meta=src_meta,
            tgt_meta=tgt_meta,
            match_result=match_res,
        )

        # 4. Uncertainty Quantification
        uncertainty_breakdown = self.unc_service.compute_uncertainty(evidence_profile)

        # 5. Serialize Keypoint Matches
        matches_payload = []
        inlier_mask = (
            evidence_profile.geometry_result.inlier_mask
            if evidence_profile.geometry_result is not None
            else np.zeros(len(match_res.source_points), dtype=bool)
        )

        for i in range(len(match_res.source_points)):
            p1 = match_res.source_points[i]
            p2 = match_res.target_points[i]
            is_in = bool(inlier_mask[i]) if i < len(inlier_mask) else False
            dist = float(match_res.match_distances[i]) if i < len(match_res.match_distances) else 0.0
            matches_payload.append({
                "src_x": float(p1[0]),
                "src_y": float(p1[1]),
                "tgt_x": float(p2[0]),
                "tgt_y": float(p2[1]),
                "is_inlier": is_in,
                "distance": dist,
            })

        corr_id = f"CORR-{src_obs_id}-{tgt_obs_id}"

        # DB Update or Create
        existing_corr = self.db.query(CorrespondenceModel).filter(CorrespondenceModel.id == corr_id).first()
        inlier_count = int(np.sum(inlier_mask))
        inlier_ratio = float(inlier_count / max(len(match_res.source_points), 1))

        if existing_corr:
            existing_corr.matcher_algorithm = matcher_name
            existing_corr.num_candidate_matches = len(match_res.source_points)
            existing_corr.num_inliers = inlier_count
            existing_corr.inlier_ratio = inlier_ratio
            existing_corr.visual_confidence = evidence_profile.visual_score
            existing_corr.overall_confidence = evidence_profile.overall_confidence
            existing_corr.status = evidence_profile.status
            existing_corr.matches_data_json = json.dumps(matches_payload)
            corr = existing_corr
        else:
            corr = CorrespondenceModel(
                id=corr_id,
                source_observation_id=src_obs_id,
                target_observation_id=tgt_obs_id,
                matcher_algorithm=matcher_name,
                num_candidate_matches=len(match_res.source_points),
                num_inliers=inlier_count,
                inlier_ratio=inlier_ratio,
                visual_confidence=evidence_profile.visual_score,
                overall_confidence=evidence_profile.overall_confidence,
                status=evidence_profile.status,
                matches_data_json=json.dumps(matches_payload),
            )
            self.db.add(corr)

        self.db.commit()
        self.db.refresh(corr)

        # Store Evidence Model
        ev_id = f"EV-{corr_id}"
        existing_ev = self.db.query(CorrespondenceEvidenceModel).filter(
            CorrespondenceEvidenceModel.correspondence_id == corr.id
        ).first()

        mean_reproj = (
            evidence_profile.geometry_result.mean_reprojection_error_px
            if evidence_profile.geometry_result is not None
            else 0.0
        )
        cond_num = (
            evidence_profile.geometry_result.condition_number
            if evidence_profile.geometry_result is not None
            else 1.0
        )

        if existing_ev:
            existing_ev.visual_score = evidence_profile.visual_score
            existing_ev.geometry_score = evidence_profile.geometry_score
            existing_ev.illumination_score = evidence_profile.illumination_score
            existing_ev.terrain_score = evidence_profile.terrain_score
            existing_ev.scale_score = evidence_profile.scale_score
            existing_ev.spatial_score = evidence_profile.spatial_score
            existing_ev.mean_reprojection_error_px = mean_reproj
            existing_ev.condition_number = cond_num
            existing_ev.total_uncertainty = uncertainty_breakdown.total_uncertainty
            existing_ev.evidence_disagreement = uncertainty_breakdown.evidence_disagreement
            existing_ev.geometric_instability = uncertainty_breakdown.geometric_instability
            existing_ev.feature_ambiguity = uncertainty_breakdown.feature_ambiguity
            existing_ev.spatial_sparsity = uncertainty_breakdown.spatial_sparsity
            existing_ev.calibration_status = uncertainty_breakdown.calibration_status
            existing_ev.rejection_reasons_json = json.dumps(evidence_profile.rejection_reasons)
            ev = existing_ev
        else:
            ev = CorrespondenceEvidenceModel(
                id=ev_id,
                correspondence_id=corr.id,
                visual_score=evidence_profile.visual_score,
                geometry_score=evidence_profile.geometry_score,
                illumination_score=evidence_profile.illumination_score,
                terrain_score=evidence_profile.terrain_score,
                scale_score=evidence_profile.scale_score,
                spatial_score=evidence_profile.spatial_score,
                mean_reprojection_error_px=mean_reproj,
                condition_number=cond_num,
                total_uncertainty=uncertainty_breakdown.total_uncertainty,
                evidence_disagreement=uncertainty_breakdown.evidence_disagreement,
                geometric_instability=uncertainty_breakdown.geometric_instability,
                feature_ambiguity=uncertainty_breakdown.feature_ambiguity,
                spatial_sparsity=uncertainty_breakdown.spatial_sparsity,
                calibration_status=uncertainty_breakdown.calibration_status,
                rejection_reasons_json=json.dumps(evidence_profile.rejection_reasons),
            )
            self.db.add(ev)

        self.db.commit()
        self.db.refresh(ev)

        return corr, ev, match_res

    def get_correspondence(self, corr_id: str) -> Optional[CorrespondenceModel]:
        return self.db.query(CorrespondenceModel).filter(CorrespondenceModel.id == corr_id).first()

    def get_evidence(self, corr_id: str) -> Optional[CorrespondenceEvidenceModel]:
        return self.db.query(CorrespondenceEvidenceModel).filter(
            CorrespondenceEvidenceModel.correspondence_id == corr_id
        ).first()

    def list_correspondences(self) -> List[CorrespondenceModel]:
        return self.db.query(CorrespondenceModel).all()
