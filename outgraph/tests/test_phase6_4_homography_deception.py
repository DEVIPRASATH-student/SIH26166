"""Phase 6.4 Adversarial Red-Team Tests: Geometric Warp / Homography Deception Attack.

Evaluates the geometric verification and physical correspondence pipeline against
deceptive and adversarial geometric transformations:
- Scenario A: Valid rigid transformation (positive control)
- Scenario B: Mild affine distortion
- Scenario C: Perspective warp
- Scenario D: Projective homography
- Scenario E: Extreme perspective homography (vanishing line in frame)
- Scenario F: Corner-folding homography (bowtie / non-convex projection)
- Scenario G: Nearly singular homography
- Scenario H: High-condition-number homography (kappa > 500)
- Scenario I: Reflection (det < 0)
- Scenario J: Rotation + reflection
- Scenario K: Anisotropic warp
- Scenario L: Local nonlinear warp (sinusoidal deformation)
- Scenario M: Piecewise deformation (discontinuous shift)
- Scenario N: Thin-plate-spline (TPS) non-rigid deformation
- Scenario O: Adversarial warp preserving feature locations (corner collapse)
- Scenario P: Warp creating false RANSAC consensus
- Scenario Q: Real OHRC/TMC-2 non-overlap and Phase 2.5 / Phase 3 preservation
"""

import pytest
import numpy as np
import cv2

from outgraph.ml.verification.geometry import (
    GeometricVerifier,
    GeometryVerificationResult,
)
from outgraph.ml.verification.scale_spatial import ScaleSpatialVerifier
from outgraph.ml.verification.physics_engine import (
    PhysicsVerificationEngine,
    PhysicsEvidenceProfile,
)
from outgraph.ml.matchers.base import MatchResult
from outgraph.ml.benchmark.metrics import BenchmarkMetrics
from outgraph.ml.benchmark.failure_classifier import (
    classify_correspondence_failure,
    CorrespondenceOutcome,
)
from outgraph.ml.data.models import (
    LunarProduct,
    ProductMetadata,
    GeographicBounds,
    ValueStatus,
    ProvenanceRecord,
    ValidationResult,
)


@pytest.fixture
def grid_keypoints():
    """Generates a well-distributed 8x8 grid of 2D points on a 512x512 image."""
    x = np.linspace(40, 472, 8)
    y = np.linspace(40, 472, 8)
    xx, yy = np.meshgrid(x, y)
    pts = np.vstack([xx.ravel(), yy.ravel()]).T.astype(np.float32)
    return pts


def apply_homography(pts: np.ndarray, H: np.ndarray) -> np.ndarray:
    """Project 2D points through a 3x3 homography matrix."""
    homo = np.hstack([pts, np.ones((len(pts), 1), dtype=np.float32)])
    proj = (H @ homo.T).T
    w = np.maximum(np.abs(proj[:, 2:3]), 1e-7)
    return (proj[:, :2] / w).astype(np.float32)


# ==============================================================================
# SCENARIOS A, B, C, D: VALID / MILD DISTORTIONS (CONTROLS)
# ==============================================================================

class TestScenariosABCD_PlausibleGeometricTransforms:
    """Verifies that physically plausible transformations are accepted or evaluated stably."""

    def test_scenario_a_valid_rigid_transformation(self, grid_keypoints):
        """Scenario A: Pure rotation (5 deg) + translation (15, 20 px)."""
        theta = np.deg2rad(5.0)
        c, s = np.cos(theta), np.sin(theta)
        H_rigid = np.array([
            [c, -s, 15.0],
            [s,  c, 20.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_rigid)

        verifier = GeometricVerifier(max_reprojection_error=4.0, max_condition_number=500.0)
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is True
        assert res.is_geometrically_stable is True
        assert res.corner_projection_valid is True
        assert res.mean_reprojection_error_px < 0.5
        assert res.condition_number < 10.0
        assert len(res.degeneracy_reasons) == 0

    def test_scenario_b_mild_affine_distortion(self, grid_keypoints):
        """Scenario B: Mild scale (1.04) + small shear (0.03) + rotation."""
        theta = np.deg2rad(2.0)
        c, s = np.cos(theta), np.sin(theta)
        A = np.array([
            [1.04 * c, -s + 0.03, 5.0],
            [s, 1.04 * c, 8.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, A)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is True
        assert res.is_geometrically_stable is True
        assert res.condition_number < 100.0

    def test_scenario_c_moderate_perspective_warp(self, grid_keypoints):
        """Scenario C: Perspective tilt with tiny projective terms."""
        H_persp = np.array([
            [1.02, 0.01, 10.0],
            [0.00, 0.98, -5.0],
            [1e-5, -2e-5, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_persp)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is True
        assert res.corner_projection_valid is True

    def test_scenario_d_projective_homography(self, grid_keypoints):
        """Scenario D: Standard well-conditioned projective homography."""
        src_corners = np.array([[50, 50], [450, 50], [450, 450], [50, 450]], dtype=np.float32)
        tgt_corners = np.array([[60, 45], [440, 55], [460, 440], [40, 455]], dtype=np.float32)
        H = cv2.getPerspectiveTransform(src_corners, tgt_corners)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is True
        assert res.is_geometrically_stable is True


# ==============================================================================
# SCENARIOS E, F, G, H: EXTREME / DEGENERATE HOMOGRAPHIES
# ==============================================================================

class TestScenariosEFGH_DegenerateHomographies:
    """Verifies rejection of ill-conditioned, vanishing pole, and folding homographies."""

    def test_scenario_e_extreme_perspective_vanishing_line_in_frame(self, grid_keypoints):
        """Scenario E: Projective term creates w' < 0.1 within image bounds."""
        # At x=250, y=250, w' = -0.004 * 250 + 1 = 0
        H_extreme = np.array([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [-0.0035, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_extreme)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.is_geometrically_stable is False
        assert any("VANISHING_LINE_IN_FRAME_POLE" in r or "EXTREME" in r for r in res.degeneracy_reasons)

    def test_scenario_f_corner_folding_homography(self):
        """Scenario F: Bowtie self-intersecting polygon projection."""
        verifier = GeometricVerifier()
        # Bowtie: p0=(50,50), p1=(450,450), p2=(450,50), p3=(50,450)
        src_corners = np.array([[50, 50], [450, 50], [450, 450], [50, 450]], dtype=np.float32)
        tgt_corners = np.array([[50, 50], [450, 450], [450, 50], [50, 450]], dtype=np.float32)
        H_fold = cv2.getPerspectiveTransform(src_corners, tgt_corners)

        pts = np.array([
            [50, 50], [450, 50], [450, 450], [50, 450],
            [250, 250], [150, 150], [350, 350], [150, 350],
        ], dtype=np.float32)
        tgt_pts = apply_homography(pts, H_fold)

        res = verifier.verify(pts, tgt_pts, image_shape=(512, 512))
        assert res.is_valid is False
        assert (res.corner_projection_valid is False or
                any("TOO_FEW_INLIERS" in r or "NON_CONVEX_FLIPPED_CORNER_PROJECTION" in r for r in res.degeneracy_reasons))

    def test_scenario_g_nearly_singular_homography(self, grid_keypoints):
        """Scenario G: Rank-deficient / nearly singular transformation matrix."""
        H_sing = np.array([
            [1.0, 2.0, 0.0],
            [2.0, 4.00001, 0.0],  # Linearly dependent row
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_sing)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.is_geometrically_stable is False
        assert any("HIGH_CONDITION_NUMBER" in r or "EXTREME_DETERMINANT" in r for r in res.degeneracy_reasons)

    def test_scenario_h_high_condition_number_homography(self, grid_keypoints):
        """Scenario H: Condition number kappa > 500 threshold."""
        H_ill = np.array([
            [10.0, 0.0, 50.0],
            [0.0, 0.005, 50.0],  # 2000x scale aspect ratio
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_ill)

        verifier = GeometricVerifier(max_condition_number=500.0)
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.condition_number > 500.0
        assert any("HIGH_CONDITION_NUMBER" in r for r in res.degeneracy_reasons)


# ==============================================================================
# SCENARIOS I, J, K: ORIENTATION FLIP / REFLECTION / ANISOTROPY
# ==============================================================================

class TestScenariosIJK_OrientationAndAnisotropy:
    """Tests reflection and anisotropic aspect-ratio attacks."""

    def test_scenario_i_pure_reflection_rejected(self, grid_keypoints):
        """Scenario I: Reflection matrix across y-axis (x -> -x)."""
        H_refl = np.array([
            [-1.0, 0.0, 512.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_refl)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.is_geometrically_stable is False
        assert (res.homography_determinant <= 0.0 or
                any("NEGATIVE_HOMOGRAPHY_DETERMINANT" in r or "EXTREME_DETERMINANT" in r or "FLIPPED" in r
                    for r in res.degeneracy_reasons))

    def test_scenario_j_rotation_plus_reflection_rejected(self, grid_keypoints):
        """Scenario J: 45-degree rotation followed by reflection (det = -1)."""
        theta = np.deg2rad(45.0)
        c, s = np.cos(theta), np.sin(theta)
        # Rotated reflection: R * diag(-1, 1)
        H_rot_refl = np.array([
            [-c, -s, 256.0],
            [-s,  c, 256.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_rot_refl)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.is_geometrically_stable is False

    def test_scenario_k_extreme_anisotropic_warp(self, grid_keypoints):
        """Scenario K: 10:1 anisotropic stretch."""
        H_aniso = np.array([
            [10.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_aniso)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.is_geometrically_stable is False


# ==============================================================================
# SCENARIOS L, M, N: NON-RIGID & NON-LINEAR WARPING
# ==============================================================================

class TestScenariosLMN_NonlinearAndNonrigidWarps:
    """Tests local non-linear, piecewise, and thin-plate-spline deformations."""

    def test_scenario_l_local_nonlinear_sinusoidal_warp(self, grid_keypoints):
        """Scenario L: Sinusoidal wave distortion cannot be fitted by planar homography."""
        src_pts = grid_keypoints
        # Apply sinusoidal deformation in x based on y: amplitude 18 px
        tgt_pts = src_pts.copy()
        tgt_pts[:, 0] += 18.0 * np.sin(src_pts[:, 1] / 30.0)

        verifier = GeometricVerifier(max_reprojection_error=4.0, min_inlier_ratio=0.60)
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        # Must fail because planar homography cannot model high-frequency sinusoidal ripple
        assert res.is_valid is False
        assert res.mean_reprojection_error_px > 4.0 or res.inlier_ratio < 0.60

    def test_scenario_m_piecewise_discontinuous_deformation(self, grid_keypoints):
        """Scenario M: Top half shifted +40 px, bottom half shifted -40 px."""
        src_pts = grid_keypoints
        tgt_pts = src_pts.copy()
        # Top half (y < 256) shifted right, bottom half shifted left
        top_mask = src_pts[:, 1] < 256.0
        tgt_pts[top_mask, 0] += 40.0
        tgt_pts[~top_mask, 0] -= 40.0

        verifier = GeometricVerifier(min_inlier_ratio=0.60)
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        # At most 50% can be inliers to any single planar transform
        assert res.is_valid is False
        assert res.inlier_ratio <= 0.55

    def test_scenario_n_thin_plate_spline_deformation(self, grid_keypoints):
        """Scenario N: Smooth non-rigid radial deformation."""
        src_pts = grid_keypoints
        center = np.array([256.0, 256.0])
        r = np.linalg.norm(src_pts - center, axis=1, keepdims=True)
        # Barrel-like radial displacement
        disp = 60.0 * (r / 256.0) ** 2 * (src_pts - center) / np.maximum(r, 1.0)
        tgt_pts = src_pts + disp

        verifier = GeometricVerifier(max_reprojection_error=4.0, min_inlier_ratio=0.50)
        res = verifier.verify(src_pts, tgt_pts.astype(np.float32), image_shape=(512, 512))

        assert res.is_valid is False
        assert res.mean_reprojection_error_px > 4.0 or res.inlier_ratio < 0.50


# ==============================================================================
# SCENARIOS O, P: ADVERSARIAL FORCED CONSENSUS & LOCALIZED CLUSTERING
# ==============================================================================

class TestScenariosOP_AdversarialConsensusAndPreservedFeatures:
    """Tests localized clustering and false consensus attempts."""

    def test_scenario_o_adversarial_warp_collapsing_frame(self, grid_keypoints):
        """Scenario O: Inliers match closely in center, but corners collapse to < 1% frame."""
        # Scale down to 0.05x (area ratio = 0.0025)
        H_collapse = np.array([
            [0.05, 0.0, 240.0],
            [0.0, 0.05, 240.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = grid_keypoints
        tgt_pts = apply_homography(src_pts, H_collapse)

        verifier = GeometricVerifier()
        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        assert res.is_valid is False
        assert res.is_geometrically_stable is False
        assert any("EXTREME_DETERMINANT" in r for r in res.degeneracy_reasons)

    def test_scenario_p_false_ransac_consensus_on_tight_cluster(self):
        """Scenario P: 6 tightly clustered collinear points cannot bypass spatial validation."""
        # 6 collinear points along x=100
        src_pts = np.array([
            [100.0, 100.0],
            [100.0, 105.0],
            [100.0, 110.0],
            [100.0, 115.0],
            [100.0, 120.0],
            [100.0, 125.0],
        ], dtype=np.float32)
        # Shifted slightly
        tgt_pts = src_pts + np.array([2.0, 2.0], dtype=np.float32)

        # ScaleSpatialVerifier checks spatial distribution and convex hull
        verifier = ScaleSpatialVerifier()
        H_ident = np.eye(3, dtype=np.float64)
        res = verifier.verify(
            src_pts=src_pts,
            tgt_pts=tgt_pts,
            inlier_mask=np.ones(6, dtype=bool),
            src_res_m=1.0,
            tgt_res_m=1.0,
            transform_matrix=H_ident,
            image_shape=(512, 512),
        )

        # Must fail spatial coverage check!
        assert res.is_valid is False
        assert res.spatial_score < 0.20 or res.convex_hull_area_ratio < 0.05


# ==============================================================================
# SCENARIO Q: PHYSICAL INVARIANTS & REGRESSION
# ==============================================================================

class TestScenarioQ_PhysicalInvariantsPreservation:
    """Verifies that mathematical homography cannot bypass physical GroundGrid gates."""

    def test_real_ohrc_tmc2_disjoint_footprints_remain_rejected(self):
        """Even with an artificially supplied identity homography, physical gates must reject."""
        from outgraph.ml.geometry.ground_grid import GroundGrid
        from outgraph.ml.geometry.dem_interface import DEMInterface
        from outgraph.ml.geometry.terrain_geometry import TerrainGeometry
        from outgraph.ml.geometry.grid_projection import GridProjector
        from outgraph.ml.geometry.target_corridor import TargetCorridorCalculator
        from outgraph.ml.matchers.physical_matcher import PhysicalCandidateEngine

        g_ohr = GroundGrid.from_csv("data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv")
        g_tmc = GroundGrid.from_csv("data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv")
        dem = DEMInterface.load_default()

        engine = PhysicalCandidateEngine(
            corridor_calc=TargetCorridorCalculator(
                projector=GridProjector(g_ohr, g_tmc),
                terrain_geo=TerrainGeometry(g_ohr, dem),
            )
        )

        cand = engine.evaluate_candidate(source_pixel=6000.0, source_scan=40000.0)
        assert cand.is_accepted is False
        assert cand.rejection_reason in {"GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH", "GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY"}
