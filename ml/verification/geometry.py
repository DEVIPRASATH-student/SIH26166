"""Geometric Consistency Verification.
Uses RANSAC to evaluate affine / projective transformations, reprojection errors,
and spatial inlier distributions.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, Any
import numpy as np
import cv2


@dataclass
class GeometryVerificationResult:
    is_valid: bool
    geometry_score: float  # [0, 1]
    inlier_mask: np.ndarray  # [N] boolean
    num_inliers: int
    inlier_ratio: float
    mean_reprojection_error_px: float
    transform_matrix: Optional[np.ndarray] = None  # 3x3 homography or 2x3 affine
    condition_number: float = 1.0
    reason: str = "Geometry verification evaluated"


class GeometricVerifier:
    """Rigorous RANSAC-based geometric constraint verifier for lunar surface imagery."""

    def __init__(
        self,
        ransac_threshold_px: float = 3.5,
        min_inliers: int = 6,
        min_inlier_ratio: float = 0.25,
        max_reprojection_error: float = 4.0,
    ):
        self.ransac_threshold = ransac_threshold_px
        self.min_inliers = min_inliers
        self.min_inlier_ratio = min_inlier_ratio
        self.max_reprojection_error = max_reprojection_error

    def verify(
        self,
        source_pts: np.ndarray,
        target_pts: np.ndarray,
        image_shape: Tuple[int, int] = (512, 512),
    ) -> GeometryVerificationResult:
        """Verifies geometric plausibility of 2D-to-2D correspondences.
        Calculates homography / affine RANSAC, inlier ratio, and reprojection error.
        """
        n = len(source_pts)
        if n < 4:
            return GeometryVerificationResult(
                is_valid=False,
                geometry_score=0.0,
                inlier_mask=np.zeros((n,), dtype=bool),
                num_inliers=0,
                inlier_ratio=0.0,
                mean_reprojection_error_px=999.0,
                reason="Insufficient matches for geometric estimation (N < 4)",
            )

        # Estimate Affine or Homography with RANSAC
        H, inliers = cv2.findHomography(
            source_pts, target_pts, cv2.RANSAC, self.ransac_threshold
        )

        if H is None or inliers is None:
            return GeometryVerificationResult(
                is_valid=False,
                geometry_score=0.0,
                inlier_mask=np.zeros((n,), dtype=bool),
                num_inliers=0,
                inlier_ratio=0.0,
                mean_reprojection_error_px=999.0,
                reason="RANSAC failed to find a valid planar projective transformation",
            )

        inlier_mask = (inliers.ravel() == 1)
        num_inliers = int(np.sum(inlier_mask))
        inlier_ratio = float(num_inliers / max(n, 1))

        if num_inliers < self.min_inliers:
            return GeometryVerificationResult(
                is_valid=False,
                geometry_score=float(np.clip(inlier_ratio * 0.5, 0.0, 0.4)),
                inlier_mask=inlier_mask,
                num_inliers=num_inliers,
                inlier_ratio=inlier_ratio,
                mean_reprojection_error_px=999.0,
                transform_matrix=H,
                reason=f"Too few geometric inliers ({num_inliers} < {self.min_inliers})",
            )

        # Compute exact reprojection error for inliers
        src_inliers = source_pts[inlier_mask]
        tgt_inliers = target_pts[inlier_mask]

        src_homo = np.hstack([src_inliers, np.ones((num_inliers, 1), dtype=np.float32)])
        projected = (H @ src_homo.T).T
        projected_pts = projected[:, :2] / np.maximum(projected[:, 2:3], 1e-7)

        errors = np.linalg.norm(projected_pts - tgt_inliers, axis=1)
        mean_error = float(np.mean(errors))

        # Check condition number of transformation matrix
        try:
            cond = float(np.linalg.cond(H))
            if np.isnan(cond) or np.isinf(cond):
                cond = 1000.0
        except Exception:
            cond = 1000.0

        # Penalize degenerate transformations (huge skew/stretch or negative determinant)
        det = np.linalg.det(H[:2, :2])
        if det <= 0.05 or det > 20.0 or cond > 500.0:
            return GeometryVerificationResult(
                is_valid=False,
                geometry_score=0.15,
                inlier_mask=inlier_mask,
                num_inliers=num_inliers,
                inlier_ratio=inlier_ratio,
                mean_reprojection_error_px=mean_error,
                transform_matrix=H,
                condition_number=cond,
                reason=f"Geometric distortion physically non-plausible (det={det:.3f}, cond={cond:.1f})",
            )

        # Calculate continuous geometry score [0, 1]
        # Inlier ratio contribution (0.5) + Error penalty (0.5)
        ratio_term = np.clip(inlier_ratio / 0.85, 0.0, 1.0)
        error_term = np.clip(1.0 - (mean_error / self.max_reprojection_error), 0.0, 1.0)
        geo_score = float(0.55 * ratio_term + 0.45 * error_term)

        is_valid = (inlier_ratio >= self.min_inlier_ratio) and (mean_error <= self.max_reprojection_error)

        return GeometryVerificationResult(
            is_valid=is_valid,
            geometry_score=geo_score,
            inlier_mask=inlier_mask,
            num_inliers=num_inliers,
            inlier_ratio=inlier_ratio,
            mean_reprojection_error_px=mean_error,
            transform_matrix=H,
            condition_number=cond,
            reason="Geometric transformation verified with acceptable reprojection residual"
            if is_valid
            else "Geometry failed: reprojection error or inlier ratio below threshold",
        )
