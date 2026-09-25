"""Phase 2 Benchmark Metric Container & Implementation Status.

Distinguishes:
  REAL        - Genuine operational algorithm implementation
  FALLBACK    - Algorithm fell back to classical baseline
  SIMULATED   - Synthetic simulation / CPU fallback
  UNAVAILABLE - Backend or weights unavailable
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


class MatcherImplementationStatus(str, Enum):
    REAL = "REAL"
    FALLBACK = "FALLBACK"
    SIMULATED = "SIMULATED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass
class BenchmarkMetrics:
    # Feature Matching Metrics
    keypoints_source: int = 0
    keypoints_target: int = 0
    candidate_matches: int = 0
    ratio_test_matches: int = 0
    geometric_inliers: int = 0
    inlier_ratio: float = 0.0

    # Geometric Residual & Stability Metrics
    mean_reprojection_error_px: float = 999.0
    median_reprojection_error_px: float = 999.0
    p95_reprojection_error_px: float = 999.0
    rmse_px: float = 999.0
    homography_condition_number: float = 1000.0
    homography_determinant: float = 0.0
    corner_projection_valid: bool = False
    is_geometrically_stable: bool = False

    # Spatial Distribution & Scale Metrics
    spatial_coverage_ratio: float = 0.0
    convex_hull_area_ratio: float = 0.0
    spatial_entropy: float = 0.0
    native_gsd_source_m: Optional[float] = None
    native_gsd_target_m: Optional[float] = None
    gsd_status: str = "UNKNOWN"
    estimated_scale_ratio: Optional[float] = None  # None if GSD UNKNOWN!
    scale_ratio_status: str = "UNKNOWN"

    # Quality & Ambiguity Metrics
    feature_ambiguity: float = 0.0
    feature_sparsity: float = 0.0
    overlap_confidence: float = 0.0

    # Matcher Metadata
    matcher_name: str = "UNKNOWN"
    matcher_implementation_status: MatcherImplementationStatus = MatcherImplementationStatus.REAL

    # Performance Timings (seconds)
    preprocessing_time_sec: float = 0.0
    matching_time_sec: float = 0.0
    verification_time_sec: float = 0.0
    total_processing_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "keypoints_source": self.keypoints_source,
            "keypoints_target": self.keypoints_target,
            "candidate_matches": self.candidate_matches,
            "ratio_test_matches": self.ratio_test_matches,
            "geometric_inliers": self.geometric_inliers,
            "inlier_ratio": round(float(self.inlier_ratio), 4),
            "mean_reprojection_error_px": round(float(self.mean_reprojection_error_px), 3),
            "median_reprojection_error_px": round(float(self.median_reprojection_error_px), 3),
            "p95_reprojection_error_px": round(float(self.p95_reprojection_error_px), 3),
            "rmse_px": round(float(self.rmse_px), 3),
            "homography_condition_number": round(float(self.homography_condition_number), 2),
            "homography_determinant": round(float(self.homography_determinant), 4),
            "corner_projection_valid": self.corner_projection_valid,
            "is_geometrically_stable": self.is_geometrically_stable,
            "spatial_coverage_ratio": round(float(self.spatial_coverage_ratio), 4),
            "convex_hull_area_ratio": round(float(self.convex_hull_area_ratio), 4),
            "spatial_entropy": round(float(self.spatial_entropy), 3),
            "native_gsd_source_m": self.native_gsd_source_m,
            "native_gsd_target_m": self.native_gsd_target_m,
            "gsd_status": self.gsd_status,
            "estimated_scale_ratio": round(float(self.estimated_scale_ratio), 4)
            if self.estimated_scale_ratio is not None
            else "UNKNOWN",
            "scale_ratio_status": self.scale_ratio_status,
            "feature_ambiguity": round(float(self.feature_ambiguity), 3),
            "feature_sparsity": round(float(self.feature_sparsity), 3),
            "overlap_confidence": round(float(self.overlap_confidence), 3),
            "matcher_name": self.matcher_name,
            "matcher_implementation_status": self.matcher_implementation_status.value,
            "preprocessing_time_sec": round(float(self.preprocessing_time_sec), 4),
            "matching_time_sec": round(float(self.matching_time_sec), 4),
            "verification_time_sec": round(float(self.verification_time_sec), 4),
            "total_processing_time_sec": round(float(self.total_processing_time_sec), 4),
        }
