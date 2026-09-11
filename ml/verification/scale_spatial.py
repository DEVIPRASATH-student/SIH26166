"""Scale and Spatial Distribution Consistency Verification.
Verifies that:
1. The estimated transformation scale matches known Ground Sampling Distance (GSD) ratios.
2. Keypoints are well-distributed across the image (spatial entropy & convex hull area)
   rather than collapsed into a single small cluster.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Any
import numpy as np
import cv2


@dataclass
class ScaleSpatialResult:
    is_valid: bool
    scale_score: float  # [0, 1]
    spatial_score: float  # [0, 1]
    estimated_scale_ratio: float
    expected_scale_ratio: float
    convex_hull_area_ratio: float
    spatial_entropy: float
    reason: str = "Scale and spatial distribution evaluated"


class ScaleSpatialVerifier:
    """Evaluates physical scale consistency and spatial distribution entropy."""

    def __init__(
        self,
        min_spatial_coverage: float = 0.04,
        max_scale_discrepancy_factor: float = 3.5,
    ):
        self.min_spatial_coverage = min_spatial_coverage
        self.max_scale_discrepancy = max_scale_discrepancy_factor

    def verify(
        self,
        src_pts: np.ndarray,
        tgt_pts: np.ndarray,
        inlier_mask: np.ndarray,
        src_res_m: float,
        tgt_res_m: float,
        transform_matrix: Optional[np.ndarray],
        image_shape: Tuple[int, int] = (512, 512),
    ) -> ScaleSpatialResult:
        """Evaluates scale ratio and spatial dispersion."""
        h, w = image_shape
        total_area = float(h * w)

        # Inlier points
        if inlier_mask is not None and np.sum(inlier_mask) >= 3:
            pts1 = src_pts[inlier_mask]
            pts2 = tgt_pts[inlier_mask]
        else:
            pts1 = src_pts
            pts2 = tgt_pts

        n = len(pts1)
        if n < 3:
            return ScaleSpatialResult(
                is_valid=False,
                scale_score=0.0,
                spatial_score=0.0,
                estimated_scale_ratio=1.0,
                expected_scale_ratio=tgt_res_m / max(src_res_m, 1e-4),
                convex_hull_area_ratio=0.0,
                spatial_entropy=0.0,
                reason="Insufficient inliers for spatial distribution analysis",
            )

        # 1. Scale consistency
        expected_scale = float(src_res_m / max(tgt_res_m, 1e-4))  # If src is 0.32m and tgt is 5.0m, scale in px is ~0.064
        if transform_matrix is not None:
            # Determinant of 2x2 affine part represents area scale factor
            det_sub = float(abs(np.linalg.det(transform_matrix[:2, :2])))
            estimated_scale = float(np.sqrt(det_sub))
        else:
            estimated_scale = 1.0

        # Discrepancy between estimated transform scale and sensor physical resolutions
        scale_ratio_divergence = max(
            estimated_scale / max(expected_scale, 1e-5),
            expected_scale / max(estimated_scale, 1e-5),
        )
        scale_score = float(
            np.clip(
                1.0 - (scale_ratio_divergence - 1.0) / self.max_scale_discrepancy,
                0.1,
                1.0,
            )
        )

        # 2. Spatial distribution (Convex Hull Area)
        try:
            hull1 = cv2.convexHull(pts1.astype(np.float32))
            area1 = float(cv2.contourArea(hull1))
            hull_ratio1 = float(np.clip(area1 / total_area, 0.0, 1.0))
        except Exception:
            hull_ratio1 = 0.05

        try:
            hull2 = cv2.convexHull(pts2.astype(np.float32))
            area2 = float(cv2.contourArea(hull2))
            hull_ratio2 = float(np.clip(area2 / total_area, 0.0, 1.0))
        except Exception:
            hull_ratio2 = 0.05

        avg_hull_ratio = float((hull_ratio1 + hull_ratio2) / 2.0)

        # 3. Spatial 2D Grid Entropy (divide image into 4x4 cells)
        grid_bins = np.zeros((4, 4), dtype=np.float32)
        cell_w, cell_h = w / 4.0, h / 4.0
        for p in pts1:
            gx = int(np.clip(p[0] // cell_w, 0, 3))
            gy = int(np.clip(p[1] // cell_h, 0, 3))
            grid_bins[gy, gx] += 1.0

        total_pts = float(np.sum(grid_bins))
        if total_pts > 0:
            probs = (grid_bins / total_pts).ravel()
            probs = probs[probs > 0]
            entropy = -float(np.sum(probs * np.log2(probs)))  # Max entropy is log2(16) = 4.0
            norm_entropy = float(np.clip(entropy / 4.0, 0.0, 1.0))
        else:
            norm_entropy = 0.0

        # Composite spatial score
        spatial_score = float(0.55 * np.clip(avg_hull_ratio / 0.35, 0.0, 1.0) + 0.45 * norm_entropy)

        is_valid = (avg_hull_ratio >= self.min_spatial_coverage) and (scale_score >= 0.25)

        reason = (
            f"Scale ({estimated_scale:.2f}x) and spatial dispersion verified (Coverage={avg_hull_ratio*100:.1f}%, Entropy={norm_entropy:.2f})"
            if is_valid
            else f"Spatial/Scale anomaly: Clustered matches ({avg_hull_ratio*100:.1f}% coverage) or resolution mismatch"
        )

        return ScaleSpatialResult(
            is_valid=is_valid,
            scale_score=scale_score,
            spatial_score=spatial_score,
            estimated_scale_ratio=estimated_scale,
            expected_scale_ratio=expected_scale,
            convex_hull_area_ratio=avg_hull_ratio,
            spatial_entropy=norm_entropy,
            reason=reason,
        )
