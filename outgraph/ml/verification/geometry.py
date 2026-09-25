"""Geometric Consistency Verification.
Uses RANSAC to evaluate affine / projective transformations, reprojection errors,
and spatial inlier distributions.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
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
    median_reprojection_error_px: float = 999.0
    p95_reprojection_error_px: float = 999.0
    homography_determinant: float = 0.0
    corner_projection_valid: bool = False
    is_geometrically_stable: bool = False
    transform_matrix: Optional[np.ndarray] = None  # 3x3 homography or 2x3 affine
    condition_number: float = 1.0
    degeneracy_reasons: List[str] = field(default_factory=list)
    reason: str = "Geometry verification evaluated"


class GeometricVerifier:
    """Rigorous RANSAC-based geometric constraint verifier for lunar surface imagery."""

    def __init__(
        self,
        ransac_threshold_px: float = 3.5,
        min_inliers: int = 6,
        min_inlier_ratio: float = 0.25,
        max_reprojection_error: float = 4.0,
        max_condition_number: float = 500.0,
    ):
        self.ransac_threshold = ransac_threshold_px
        self.min_inliers = min_inliers
        self.min_inlier_ratio = min_inlier_ratio
        self.max_reprojection_error = max_reprojection_error
        self.max_condition_number = max_condition_number

    def verify(
        self,
        source_pts: np.ndarray,
        target_pts: np.ndarray,
        image_shape: Tuple[int, int] = (512, 512),
    ) -> GeometryVerificationResult:
        """Verifies geometric plausibility of 2D-to-2D correspondences.
        Calculates homography / affine RANSAC, inlier ratio, reprojection error, and degeneracy.
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
                median_reprojection_error_px=999.0,
                p95_reprojection_error_px=999.0,
                degeneracy_reasons=["INSUFFICIENT_MATCHES"],
                reason="Insufficient matches for geometric estimation (N < 4)",
            )

        # Estimate Homography with RANSAC
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
                median_reprojection_error_px=999.0,
                p95_reprojection_error_px=999.0,
                degeneracy_reasons=["RANSAC_ESTIMATION_FAILED"],
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
                median_reprojection_error_px=999.0,
                p95_reprojection_error_px=999.0,
                transform_matrix=H,
                degeneracy_reasons=["TOO_FEW_INLIERS"],
                reason=f"Too few geometric inliers ({num_inliers} < {self.min_inliers})",
            )

        # Compute exact reprojection error for inliers
        src_inliers = source_pts[inlier_mask]
        tgt_inliers = target_pts[inlier_mask]

        src_homo = np.hstack([src_inliers, np.ones((num_inliers, 1), dtype=np.float32)])
        projected = (H @ src_homo.T).T

        # Check homogeneous denominator w' = H_31*x + H_32*y + H_33
        w_denom = projected[:, 2]
        denom_collapse = np.any(np.abs(w_denom) < 0.1)

        projected_pts = projected[:, :2] / np.maximum(np.abs(projected[:, 2:3]), 1e-7)
        errors = np.linalg.norm(projected_pts - tgt_inliers, axis=1)

        mean_error = float(np.mean(errors))
        median_error = float(np.median(errors))
        p95_error = float(np.percentile(errors, 95)) if len(errors) > 0 else mean_error

        # Check condition number of transformation matrix (scale-invariant normalized)
        h_src, w_src = image_shape
        scale_norm = max(float(h_src), float(w_src), 1.0)
        T_norm = np.array([
            [1.0 / scale_norm, 0.0, 0.0],
            [0.0, 1.0 / scale_norm, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)
        T_inv = np.array([
            [scale_norm, 0.0, 0.0],
            [0.0, scale_norm, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)
        H_norm = T_norm @ H @ T_inv

        try:
            cond = float(np.linalg.cond(H_norm))
            if np.isnan(cond) or np.isinf(cond):
                cond = 1e12
        except Exception:
            cond = 1e12

        # Check determinant of 2x2 affine portion
        det = float(np.linalg.det(H[:2, :2]))

        # Check anisotropic stretch ratio
        try:
            _, s_vals, _ = np.linalg.svd(H[:2, :2])
            aspect_ratio = float(s_vals[0] / max(s_vals[1], 1e-7))
        except Exception:
            aspect_ratio = 1.0

        # Corner projection sanity check (verify corners form valid convex polygon)
        corners_src = np.array([
            [0.0, 0.0],
            [w_src, 0.0],
            [w_src, h_src],
            [0.0, h_src],
        ], dtype=np.float32)

        corners_homo = np.hstack([corners_src, np.ones((4, 1), dtype=np.float32)])
        proj_corners_h = (H @ corners_homo.T).T
        corner_w_collapse = np.any(np.abs(proj_corners_h[:, 2]) < 0.1)

        proj_corners = proj_corners_h[:, :2] / np.maximum(np.abs(proj_corners_h[:, 2:3]), 1e-7)

        # Convexity & winding orientation check
        corner_valid = False
        if not corner_w_collapse:
            try:
                hull = cv2.convexHull(proj_corners.astype(np.float32))
                area_src = cv2.contourArea(corners_src, oriented=True)
                area_proj = cv2.contourArea(proj_corners.astype(np.float32), oriented=True)
                orientation_preserved = (area_src * area_proj > 0)
                is_convex = (len(hull) == 4) and cv2.isContourConvex(proj_corners.astype(np.float32))
                corner_valid = bool(is_convex and orientation_preserved)
            except Exception:
                corner_valid = False

        # Flag explicit degeneracy conditions
        degeneracies: List[str] = []
        if cond > self.max_condition_number:
            degeneracies.append(f"HIGH_CONDITION_NUMBER (kappa={cond:.1e})")
        if det <= 0.01 or det > 100.0:
            degeneracies.append(f"EXTREME_DETERMINANT (det={det:.3f})")
        if np.linalg.det(H) <= 0:
            degeneracies.append("NEGATIVE_HOMOGRAPHY_DETERMINANT")
        if aspect_ratio > 4.0:
            degeneracies.append(f"EXTREME_ANISOTROPIC_DISTORTION (ratio={aspect_ratio:.2f})")
        if denom_collapse or corner_w_collapse:
            degeneracies.append("VANISHING_LINE_IN_FRAME_POLE")
        if not corner_valid:
            degeneracies.append("NON_CONVEX_FLIPPED_CORNER_PROJECTION")
        if mean_error > 20.0 or median_error > 10.0:
            degeneracies.append(f"EXTREME_REPROJECTION_RESIDUAL (mean={mean_error:.1f}px, median={median_error:.1f}px)")
        if p95_error > 25.0:
            degeneracies.append(f"EXTREME_TAIL_RESIDUAL (p95={p95_error:.1f}px)")

        is_stable = (len(degeneracies) == 0) and (inlier_ratio >= self.min_inlier_ratio) and (mean_error <= self.max_reprojection_error)

        if len(degeneracies) > 0:
            return GeometryVerificationResult(
                is_valid=False,
                geometry_score=0.10,
                inlier_mask=inlier_mask,
                num_inliers=num_inliers,
                inlier_ratio=inlier_ratio,
                mean_reprojection_error_px=mean_error,
                median_reprojection_error_px=median_error,
                p95_reprojection_error_px=p95_error,
                homography_determinant=det,
                corner_projection_valid=corner_valid,
                is_geometrically_stable=False,
                transform_matrix=H,
                condition_number=cond,
                degeneracy_reasons=degeneracies,
                reason=f"Geometric transformation degenerate: {', '.join(degeneracies)}",
            )

        # Calculate continuous geometry score [0, 1]
        ratio_term = np.clip(inlier_ratio / 0.85, 0.0, 1.0)
        error_term = np.clip(1.0 - (mean_error / self.max_reprojection_error), 0.0, 1.0)
        geo_score = float(0.55 * ratio_term + 0.45 * error_term)

        return GeometryVerificationResult(
            is_valid=is_stable,
            geometry_score=geo_score,
            inlier_mask=inlier_mask,
            num_inliers=num_inliers,
            inlier_ratio=inlier_ratio,
            mean_reprojection_error_px=mean_error,
            median_reprojection_error_px=median_error,
            p95_reprojection_error_px=p95_error,
            homography_determinant=det,
            corner_projection_valid=corner_valid,
            is_geometrically_stable=is_stable,
            transform_matrix=H,
            condition_number=cond,
            degeneracy_reasons=[],
            reason="Geometric transformation verified with acceptable reprojection residual"
            if is_stable
            else "Geometry failed: reprojection error or inlier ratio below threshold",
        )
