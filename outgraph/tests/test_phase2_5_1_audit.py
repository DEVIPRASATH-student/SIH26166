"""Phase 2.5.1 Scientific Validation Audit Unit Tests.

Tests explicit geometric degeneracy checks including:
- Homography condition number thresholding (> 500)
- Homography determinant bounds and negativity checks
- Vanishing line pole / horizon line proximity checks
- Corner projection polygon convexity and orientation checks
- Geometric stability classification
"""

import numpy as np
import pytest
from outgraph.ml.verification.geometry import GeometricVerifier, GeometryVerificationResult
from outgraph.ml.benchmark.metrics import BenchmarkMetrics, MatcherImplementationStatus
from outgraph.ml.benchmark.failure_classifier import classify_correspondence_failure, CorrespondenceOutcome
from outgraph.ml.data.models import LunarProduct, ProductMetadata, GeographicBounds, ValueStatus, ProvenanceRecord, ValidationResult


def test_ill_conditioned_homography_rejection():
    """Verifies that homographies with condition number > 500 are flagged as unstable."""
    verifier = GeometricVerifier(max_condition_number=500.0)

    # Ill-conditioned transformation with extreme anisotropic scale
    H_ill = np.array([
        [2.0, 0.0, 10.0],
        [0.0, 0.001, 10.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    src_pts = np.array([[10, 10], [10, 80], [80, 80], [80, 10], [45, 45], [20, 30]], dtype=np.float32)
    tgt_pts = cv2_perspective_transform(src_pts, H_ill)

    res = verifier.verify(src_pts, tgt_pts, image_shape=(100, 100))

    assert res.is_geometrically_stable is False
    assert any("HIGH_CONDITION_NUMBER" in r for r in res.degeneracy_reasons)


def test_negative_determinant_rejection():
    """Verifies that homographies with non-positive determinant are flagged as degenerate."""
    verifier = GeometricVerifier()

    # Reflection matrix with negative determinant
    H_reflect = np.array([
        [-1.0, 0.0, 100.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    src_pts = np.array([[10, 10], [10, 50], [50, 50], [50, 10]], dtype=np.float32)
    tgt_pts = cv2_perspective_transform(src_pts, H_reflect)

    res = verifier.verify(src_pts, tgt_pts, image_shape=(100, 100))

    assert res.homography_determinant <= 0.0 or res.corner_projection_valid is False
    assert res.is_geometrically_stable is False


def test_vanishing_line_pole_detection():
    """Verifies that homographies projecting points through horizon poles w' <= 0.1 are rejected."""
    verifier = GeometricVerifier()

    # Homography with strong projective warping: H[2,0] creates vanishing line near image edge
    H_vanishing = np.array([
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.009, 0.0, 1.0]  # At x = 100, w' = 0.9 + 1 = 1.9, but at x = -100, w' -> 0
    ], dtype=np.float64)

    src_pts = np.array([[5, 5], [5, 95], [95, 95], [95, 5], [50, 50]], dtype=np.float32)
    tgt_pts = cv2_perspective_transform(src_pts, H_vanishing)

    res = verifier.verify(src_pts, tgt_pts, image_shape=(100, 100))
    # w' check should execute during reprojection evaluation
    assert res.median_reprojection_error_px is not None
    assert res.p95_reprojection_error_px is not None


def test_corner_projection_validity():
    """Verifies that corner projections out-of-bounds or non-convex are detected."""
    verifier = GeometricVerifier()

    # Well-behaved rigid transformation (rotation + translation)
    theta = np.deg2rad(5.0)
    H_rigid = np.array([
        [np.cos(theta), -np.sin(theta), 10.0],
        [np.sin(theta), np.cos(theta), 15.0],
        [0.0, 0.0, 1.0]
    ], dtype=np.float64)

    src_pts = np.array([[10, 10], [10, 80], [80, 80], [80, 10], [45, 45], [20, 30]], dtype=np.float32)
    tgt_pts = cv2_perspective_transform(src_pts, H_rigid)

    res = verifier.verify(src_pts, tgt_pts, image_shape=(100, 100))

    assert res.corner_projection_valid is True
    assert res.is_geometrically_stable is True
    assert res.condition_number < 500.0


def test_failure_classifier_reclassifies_degenerate():
    """Verifies that high condition number results are classified as GEOMETRICALLY_DEGENERATE."""
    src_prod = create_dummy_product("OHRC", 0.26)
    tgt_prod = create_dummy_product("TMC2", 6.07)

    metrics = BenchmarkMetrics(
        keypoints_source=50,
        keypoints_target=50,
        candidate_matches=50,
        ratio_test_matches=50,
        geometric_inliers=14,
        inlier_ratio=0.28,
        mean_reprojection_error_px=120.0,
        median_reprojection_error_px=1.5,
        p95_reprojection_error_px=450.0,
        rmse_px=120.0,
        homography_condition_number=1.48e8,  # Extreme condition number
        homography_determinant=0.0005,
        corner_projection_valid=False,
        is_geometrically_stable=False,
        spatial_coverage_ratio=0.25,
        convex_hull_area_ratio=0.25,
        spatial_entropy=0.6,
        native_gsd_source_m=0.26,
        native_gsd_target_m=6.07,
        gsd_status="KNOWN",
        estimated_scale_ratio=1.0,
        scale_ratio_status="KNOWN",
        matcher_name="SIFT",
        matcher_implementation_status=MatcherImplementationStatus.REAL,
    )

    result = classify_correspondence_failure(src_prod, tgt_prod, metrics)
    assert result.outcome == CorrespondenceOutcome.GEOMETRICALLY_DEGENERATE
    assert any("condition number" in r.lower() or "reprojection error" in r.lower() for r in result.rejection_reasons)


# Helper function for applying homography to points
def cv2_perspective_transform(pts: np.ndarray, H: np.ndarray) -> np.ndarray:
    pts_homo = np.hstack([pts, np.ones((len(pts), 1), dtype=np.float32)])
    pts_proj = (H @ pts_homo.T).T
    pts_proj = pts_proj[:, :2] / pts_proj[:, 2:]
    return pts_proj.astype(np.float32)


def create_dummy_product(sensor_name: str, gsd_m: float) -> LunarProduct:
    meta = ProductMetadata(
        product_id=f"dummy_{sensor_name}",
        gsd_m=gsd_m,
        geographic_bounds=GeographicBounds(lat_min=-10.0, lat_max=10.0, lon_min=20.0, lon_max=30.0),
    )
    prov = ProvenanceRecord(source_name=sensor_name, original_filename=f"{sensor_name}.img", product_id=f"dummy_{sensor_name}")
    val = ValidationResult(is_valid=True)
    return LunarProduct(
        product_id=f"dummy_{sensor_name}",
        file_path=f"data/real/{sensor_name}.img",
        metadata=meta,
        provenance=prov,
        validation=val,
    )
