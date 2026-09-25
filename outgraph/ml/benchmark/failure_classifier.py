"""Phase 2 Correspondence Failure Classifier & Outcome Decision Engine.

Classifies correspondence outcomes into ACCEPTED, REJECTED, AMBIGUOUS, INSUFFICIENT_EVIDENCE.
Identifies dominant and secondary failure categories based on measurable empirical evidence.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import numpy as np

from .metrics import BenchmarkMetrics
from ..data.models import LunarProduct, ValueStatus


class CorrespondenceOutcome(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    GEOMETRICALLY_DEGENERATE = "GEOMETRICALLY_DEGENERATE"
    GEOMETRICALLY_STABLE = "GEOMETRICALLY_STABLE"
    CORRESPONDENCE_NOT_VALIDATED = "CORRESPONDENCE_NOT_VALIDATED"


class FailureCategory(str, Enum):
    DATA_AVAILABILITY = "DATA_AVAILABILITY"
    GEOMETRIC_FAILURE = "GEOMETRIC_FAILURE"
    REGISTRATION_FAILURE = "REGISTRATION_FAILURE"
    CORRESPONDENCE_UNCERTAINTY = "CORRESPONDENCE_UNCERTAINTY"
    SCALE_FAILURE = "SCALE_FAILURE"
    ILLUMINATION_FAILURE = "ILLUMINATION_FAILURE"
    CROSS_MODAL_FAILURE = "CROSS_MODAL_FAILURE"
    LOW_TEXTURE_FAILURE = "LOW_TEXTURE_FAILURE"
    REPETITIVE_TERRAIN_FAILURE = "REPETITIVE_TERRAIN_FAILURE"
    OVERLAP_FAILURE = "OVERLAP_FAILURE"
    METADATA_UNCERTAINTY = "METADATA_UNCERTAINTY"
    FEATURE_SPARSITY_FAILURE = "FEATURE_SPARSITY_FAILURE"
    FALSE_CORRESPONDENCE_RISK = "FALSE_CORRESPONDENCE_RISK"
    COMPUTATIONAL_FAILURE = "COMPUTATIONAL_FAILURE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    UNKNOWN = "UNKNOWN"


@dataclass
class FailureAnalysisResult:
    outcome: CorrespondenceOutcome
    dominant_failure: Optional[FailureCategory]
    secondary_failure: Optional[FailureCategory]
    rejection_reasons: List[str]
    evidence_breakdown: Dict[str, Any]
    explanation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "outcome": self.outcome.value,
            "dominant_failure": self.dominant_failure.value if self.dominant_failure else None,
            "secondary_failure": self.secondary_failure.value if self.secondary_failure else None,
            "rejection_reasons": self.rejection_reasons,
            "evidence_breakdown": self.evidence_breakdown,
            "explanation": self.explanation,
        }


def classify_correspondence_failure(
    source_product: LunarProduct,
    target_product: LunarProduct,
    metrics: BenchmarkMetrics,
    min_inliers: int = 8,
    min_inlier_ratio: float = 0.25,
    max_reprojection_error: float = 4.0,
    min_spatial_coverage: float = 0.04,
) -> FailureAnalysisResult:
    """Evaluates correspondence metrics and classifies outcome + failure categories."""
    rejection_reasons: List[str] = []
    detected_failures: List[Tuple[FailureCategory, float]] = []  # (Category, Severity score [0, 1])

    # 1. Feature Sparsity & Candidate Check
    if metrics.keypoints_source < 10 or metrics.keypoints_target < 10:
        rejection_reasons.append(
            f"Feature Sparsity: Extremely low keypoint extraction count (Src: {metrics.keypoints_source}, Tgt: {metrics.keypoints_target})"
        )
        detected_failures.append((FailureCategory.FEATURE_SPARSITY_FAILURE, 0.9))

    if metrics.candidate_matches < 4:
        rejection_reasons.append(
            f"Insufficient Candidate Matches: Only {metrics.candidate_matches} raw candidate matches found"
        )
        detected_failures.append((FailureCategory.FEATURE_SPARSITY_FAILURE, 0.95))

    # 2. Geometric Inliers & Reprojection Error Check
    if metrics.geometric_inliers < min_inliers:
        rejection_reasons.append(
            f"Low Inlier Count: {metrics.geometric_inliers} inliers found (< {min_inliers} required minimum)"
        )
        detected_failures.append((FailureCategory.GEOMETRIC_FAILURE, 0.85))

    if metrics.inlier_ratio < min_inlier_ratio:
        rejection_reasons.append(
            f"Low Inlier Ratio: {metrics.inlier_ratio:.1%} inliers (< {min_inlier_ratio:.1%} required)"
        )
        detected_failures.append((FailureCategory.GEOMETRIC_FAILURE, 0.80))

    if metrics.mean_reprojection_error_px > max_reprojection_error:
        rejection_reasons.append(
            f"High Reprojection Error: {metrics.mean_reprojection_error_px:.2f} px mean residual (> {max_reprojection_error:.1f} px threshold)"
        )
        detected_failures.append((FailureCategory.GEOMETRIC_FAILURE, 0.88))

    if metrics.homography_condition_number > 500.0:
        rejection_reasons.append(
            f"Unstable Transformation Matrix: Homography condition number = {metrics.homography_condition_number:.1f} (> 500.0)"
        )
        detected_failures.append((FailureCategory.GEOMETRIC_FAILURE, 0.75))

    # 3. Spatial Dispersion Check (Clustered Boulder / Degenerate Trap)
    if metrics.convex_hull_area_ratio < min_spatial_coverage and metrics.geometric_inliers >= min_inliers:
        rejection_reasons.append(
            f"Spatial Coverage Collapse: Inliers cover only {metrics.convex_hull_area_ratio*100:.2f}% of frame (< {min_spatial_coverage*100:.1f}% minimum)"
        )
        detected_failures.append((FailureCategory.FALSE_CORRESPONDENCE_RISK, 0.92))

    # 4. Modality Mismatch Check
    src_inst = (source_product.metadata.instrument or "").upper()
    tgt_inst = (target_product.metadata.instrument or "").upper()
    if "IIRS" in src_inst or "IIRS" in tgt_inst:
        if src_inst != tgt_inst:
            rejection_reasons.append(
                "Cross-Modal Ambiguity: IIRS spectral imagery vs panchromatic optical camera mismatch"
            )
            detected_failures.append((FailureCategory.CROSS_MODAL_FAILURE, 0.70))

    # 5. Metadata Uncertainty Check
    src_gsd_status = source_product.metadata.value_statuses.get("gsd_m", ValueStatus.UNKNOWN)
    tgt_gsd_status = target_product.metadata.value_statuses.get("gsd_m", ValueStatus.UNKNOWN)
    if src_gsd_status == ValueStatus.UNKNOWN or tgt_gsd_status == ValueStatus.UNKNOWN:
        rejection_reasons.append(
            "Metadata Uncertainty: Native GSD is UNKNOWN for one or both products"
        )
        detected_failures.append((FailureCategory.METADATA_UNCERTAINTY, 0.50))

    # 6. Solar Illumination Divergence Check
    src_sun = source_product.metadata.solar_illumination
    tgt_sun = target_product.metadata.solar_illumination
    if (
        src_sun.status == ValueStatus.KNOWN
        and tgt_sun.status == ValueStatus.KNOWN
        and src_sun.sun_azimuth_deg is not None
        and tgt_sun.sun_azimuth_deg is not None
    ):
        az_diff = abs(src_sun.sun_azimuth_deg - tgt_sun.sun_azimuth_deg) % 360.0
        if az_diff > 180.0:
            az_diff = 360.0 - az_diff
        if az_diff > 90.0:
            rejection_reasons.append(
                f"Severe Solar Illumination Shift: Sun azimuth difference ΔAz = {az_diff:.1f}°"
            )
            detected_failures.append((FailureCategory.ILLUMINATION_FAILURE, 0.80))

    # Determine Outcome & Primary Failure
    if len(rejection_reasons) == 0:
        outcome = CorrespondenceOutcome.GEOMETRICALLY_STABLE if metrics.is_geometrically_stable else CorrespondenceOutcome.ACCEPTED
        explanation = "Correspondence successfully verified across visual, geometric, and spatial distribution metrics."
        dominant_failure = None
        secondary_failure = None
    else:
        # Sort detected failures by severity score descending
        detected_failures.sort(key=lambda x: x[1], reverse=True)
        dominant_failure = detected_failures[0][0] if detected_failures else FailureCategory.UNKNOWN
        secondary_failure = detected_failures[1][0] if len(detected_failures) > 1 else None

        if metrics.geometric_inliers < 4:
            outcome = CorrespondenceOutcome.INSUFFICIENT_EVIDENCE
            explanation = "Insufficient feature matches to form a scientifically valid correspondence hypothesis."
        elif not metrics.is_geometrically_stable and metrics.geometric_inliers >= 4:
            outcome = CorrespondenceOutcome.GEOMETRICALLY_DEGENERATE
            explanation = f"Candidate matches produce ill-conditioned or non-plausible planar homography: {rejection_reasons[0]}"
        elif metrics.inlier_ratio >= 0.15 and metrics.geometric_inliers >= 5:
            outcome = CorrespondenceOutcome.AMBIGUOUS
            explanation = "Candidate matches exhibit partial geometric alignment but exceed residual or spatial entropy limits."
        else:
            outcome = CorrespondenceOutcome.REJECTED
            explanation = f"Correspondence rejected due to {dominant_failure.value}: {rejection_reasons[0]}"

    evidence_breakdown = {
        "candidate_matches": metrics.candidate_matches,
        "inliers": metrics.geometric_inliers,
        "inlier_ratio": metrics.inlier_ratio,
        "mean_reprojection_error_px": metrics.mean_reprojection_error_px,
        "spatial_coverage_ratio": metrics.convex_hull_area_ratio,
        "condition_number": metrics.homography_condition_number,
        "gsd_status": metrics.gsd_status,
        "detected_failure_count": len(detected_failures),
    }

    return FailureAnalysisResult(
        outcome=outcome,
        dominant_failure=dominant_failure,
        secondary_failure=secondary_failure,
        rejection_reasons=rejection_reasons,
        evidence_breakdown=evidence_breakdown,
        explanation=explanation,
    )
