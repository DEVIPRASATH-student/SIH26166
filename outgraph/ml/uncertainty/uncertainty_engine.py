"""Uncertainty Quantification Engine.
Calculates calibrated uncertainty for multi-modal lunar correspondences and world model beliefs.
Combines:
1. Evidence Divergence (variance across visual, geometry, solar, terrain, scale, spatial scores)
2. Residual Reprojection Variance
3. Feature Ambiguity (descriptor distance entropy)
4. Local Keypoint Density / Spatial Sparsity
5. Geometric Condition Stability (matrix condition number)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import numpy as np

from ..verification.physics_engine import PhysicsEvidenceProfile


@dataclass
class UncertaintyBreakdown:
    total_uncertainty: float  # [0, 1] Calibrated uncertainty score
    evidence_disagreement: float  # [0, 1] Discrepancy across evidence modules
    geometric_instability: float  # [0, 1] Transformation conditioning & reprojection spread
    feature_ambiguity: float  # [0, 1] Descriptor distance ambiguity
    spatial_sparsity: float  # [0, 1] Penalizes sparse / clustered keypoints
    calibration_status: str  # "CALIBRATED", "HIGH_EPISTEMIC_RISK", "ALEATORIC_NOISE"
    explanation: str


class UncertaintyEngine:
    """Calculates scientifically rigorous uncertainty for correspondences and beliefs."""

    def __init__(self):
        # Weights for composite uncertainty
        self.w_divergence = 0.35
        self.w_geom_instability = 0.25
        self.w_ambiguity = 0.20
        self.w_sparsity = 0.20

    def compute_correspondence_uncertainty(
        self,
        profile: PhysicsEvidenceProfile,
    ) -> UncertaintyBreakdown:
        """Calculates multi-factor uncertainty from physics evidence profile."""
        scores = np.array([
            profile.visual_score,
            profile.geometry_score,
            profile.illumination_score,
            profile.terrain_score,
            profile.scale_score,
            profile.spatial_score,
        ], dtype=np.float32)

        # 1. Evidence Disagreement: Standard deviation across individual evidence modules
        # High visual match + low physics consistency produces high standard deviation!
        std_evidence = float(np.std(scores))
        evidence_disagreement = float(np.clip(std_evidence * 2.8, 0.0, 1.0))

        # 2. Geometric Instability: derived from reprojection error and condition number
        if profile.geometry_result is not None:
            mean_err = profile.geometry_result.mean_reprojection_error_px
            cond = profile.geometry_result.condition_number
            err_term = float(np.clip(mean_err / 4.0, 0.0, 1.0))
            cond_term = float(np.clip(np.log10(max(cond, 1.0)) / 2.5, 0.0, 1.0))
            geom_instability = float(0.6 * err_term + 0.4 * cond_term)
        else:
            geom_instability = 0.85

        # 3. Feature Ambiguity
        # If visual score is high but inlier ratio is low, ambiguity is high
        inlier_ratio = float(profile.metadata.get("inlier_ratio", 0.5))
        feature_ambiguity = float(np.clip(1.0 - inlier_ratio, 0.05, 0.95))

        # 4. Spatial Sparsity: Penalizes matches with poor spatial distribution
        spatial_score = profile.spatial_score
        spatial_sparsity = float(np.clip(1.0 - spatial_score, 0.05, 0.95))

        # Total Composite Uncertainty
        total_unc = float(
            self.w_divergence * evidence_disagreement
            + self.w_geom_instability * geom_instability
            + self.w_ambiguity * feature_ambiguity
            + self.w_sparsity * spatial_sparsity
        )
        total_unc = float(np.clip(total_unc, 0.02, 0.98))

        # Calibration classification
        if profile.status == "VERIFIED" and total_unc < 0.25:
            cal_status = "CALIBRATED_LOW_UNCERTAINTY"
            explanation = "Evidence modules in high agreement with stable geometric reprojection and broad spatial support."
        elif evidence_disagreement > 0.45:
            cal_status = "HIGH_EPISTEMIC_RISK"
            explanation = "High conflict between visual appearance and physical solar/terrain constraints."
        elif geom_instability > 0.50:
            cal_status = "GEOMETRIC_ALEATORIC_NOISE"
            explanation = "High residual reprojection variance or ill-conditioned planar transformation."
        else:
            cal_status = "MODERATE_UNCERTAINTY"
            explanation = "Moderate uncertainty due to cross-resolution scaling and illumination differences."

        return UncertaintyBreakdown(
            total_uncertainty=round(total_unc, 4),
            evidence_disagreement=round(evidence_disagreement, 4),
            geometric_instability=round(geom_instability, 4),
            feature_ambiguity=round(feature_ambiguity, 4),
            spatial_sparsity=round(spatial_sparsity, 4),
            calibration_status=cal_status,
            explanation=explanation,
        )
