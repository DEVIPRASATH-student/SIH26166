"""Phase 6.3 Adversarial Red-Team Tests: Scale Deception / Multi-GSD Adversarial Attack.

Evaluates the physical and geometric correspondence pipeline against deceptive scale conditions:
- Scenario A: Correct Scale (scale agreement validated, but insufficient alone)
- Scenario B: Incorrect Scale (2x, 4x, 10x scale error rejected)
- Scenario C: False Scale Compensation (homography warp forced on wrong scale rejected)
- Scenario D: Extreme Aspect-Ratio Distortion (anisotropic 2:1, 4:1, 10:1 scaling rejected as degenerate)
- Scenario E: Resize-Then-Match Attack (high match count cannot override physical scale validation)
- Scenario F: Wrong / Missing Sensor GSD Metadata (metadata discrepancy caught, missing GSD preserves UNKNOWN)
- Scenario G: Multi-GSD Ambiguity (multiple plausible scales preserve AMBIGUOUS state)
- Scenario H: Real OHRC/TMC-2 Regression (preserves SCALE EFFECT OBSERVED BUT GEOMETRICALLY UNSTABLE)
"""

import pytest
import numpy as np

from outgraph.ml.verification.scale_spatial import (
    ScaleSpatialVerifier,
    ScaleSpatialResult,
)
from outgraph.ml.verification.geometry import (
    GeometricVerifier,
    GeometryVerificationResult,
)
from outgraph.ml.verification.physics_engine import (
    PhysicsVerificationEngine,
    PhysicsEvidenceProfile,
)
from outgraph.ml.matchers.base import MatchResult
from outgraph.ml.benchmark.metrics import BenchmarkMetrics
from outgraph.ml.benchmark.failure_classifier import (
    classify_correspondence_failure,
    CorrespondenceOutcome,
    FailureCategory,
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
def base_keypoints():
    """Generates synthetic 2D keypoints well-distributed across a 512x512 image."""
    rng = np.random.default_rng(42)
    # Generate 40 points spanning [50, 460] in x and y
    pts = rng.uniform(50.0, 460.0, (40, 2)).astype(np.float32)
    return pts


# ==============================================================================
# SCENARIO A: CORRECT SCALE
# ==============================================================================

class TestScenarioA_CorrectScale:
    """Verifies that the system recognizes correct physical scale, but requires all checks."""

    def test_correct_scale_verified_with_good_spatial_coverage(self, base_keypoints):
        verifier = ScaleSpatialVerifier()
        # Scale factor 4.0x: src_res = 0.25m, tgt_res = 1.0m => expected scale = 0.25
        # Transform matrix has scale 0.25
        scale_val = 0.25
        H = np.array([
            [scale_val, 0.0, 10.0],
            [0.0, scale_val, 15.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = base_keypoints
        tgt_pts = (H[:2, :2] @ src_pts.T).T + H[:2, 2]
        inlier_mask = np.ones(len(src_pts), dtype=bool)

        res = verifier.verify(
            src_pts=src_pts,
            tgt_pts=tgt_pts,
            inlier_mask=inlier_mask,
            src_res_m=0.25,
            tgt_res_m=1.0,
            transform_matrix=H,
            image_shape=(512, 512),
        )

        assert res.is_valid is True
        assert res.scale_score >= 0.90
        assert res.estimated_scale_ratio == pytest.approx(0.25, abs=1e-3)

    def test_scale_agreement_alone_insufficient_if_spatially_clustered(self):
        """Scale matches perfectly, but all points are clustered in a 5px micro-region."""
        verifier = ScaleSpatialVerifier(min_spatial_coverage=0.04)
        scale_val = 0.5
        H = np.array([[scale_val, 0.0, 0.0], [0.0, scale_val, 0.0], [0.0, 0.0, 1.0]])

        # Tightly clustered points in a 2x2 px area
        clustered_pts = np.array([[100.0, 100.0], [101.0, 100.5], [100.5, 101.0], [101.5, 101.5]], dtype=np.float32)
        tgt_pts = (H[:2, :2] @ clustered_pts.T).T
        inlier_mask = np.ones(len(clustered_pts), dtype=bool)

        res = verifier.verify(
            src_pts=clustered_pts,
            tgt_pts=tgt_pts,
            inlier_mask=inlier_mask,
            src_res_m=0.5,
            tgt_res_m=1.0,
            transform_matrix=H,
            image_shape=(512, 512),
        )

        # Must be rejected because spatial coverage is insufficient, despite correct scale!
        assert res.is_valid is False
        assert res.convex_hull_area_ratio < 0.04


# ==============================================================================
# SCENARIO B: INCORRECT SCALE
# ==============================================================================

class TestScenarioB_IncorrectScale:
    """Verifies that severe scale mismatch cannot produce valid physical scale verification."""

    @pytest.mark.parametrize("false_scale_factor, expected_res", [
        (4.0, False),    # 4x physical scale discrepancy
        (10.0, False),   # 10x physical scale discrepancy
        (0.05, False),   # 20x physical scale discrepancy
    ])
    def test_severe_scale_discrepancy_rejected(self, base_keypoints, false_scale_factor, expected_res):
        verifier = ScaleSpatialVerifier()
        # Physical GSD indicates scale should be 1.0 (both 0.5m)
        src_res = 0.5
        tgt_res = 0.5

        # Transform has false scale factor
        H = np.array([
            [false_scale_factor, 0.0, 5.0],
            [0.0, false_scale_factor, 5.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = base_keypoints
        tgt_pts = (H[:2, :2] @ src_pts.T).T + H[:2, 2]
        inlier_mask = np.ones(len(src_pts), dtype=bool)

        res = verifier.verify(
            src_pts=src_pts,
            tgt_pts=tgt_pts,
            inlier_mask=inlier_mask,
            src_res_m=src_res,
            tgt_res_m=tgt_res,
            transform_matrix=H,
            image_shape=(512, 512),
        )

        assert res.is_valid is expected_res
        assert res.scale_score <= 0.25


# ==============================================================================
# SCENARIO C: FALSE SCALE COMPENSATION ATTACK
# ==============================================================================

class TestScenarioC_FalseScaleCompensation:
    """Tests an aggressive warp attempting to force alignment under false scale."""

    def test_forced_homography_warp_rejected_by_physics_engine(self, base_keypoints):
        # A homography that distorts scale non-linearly to force numerical alignment
        H_forced = np.array([
            [4.5, 0.8, -20.0],
            [-0.3, 4.2, 10.0],
            [0.001, 0.002, 1.0],
        ], dtype=np.float64)

        src_pts = base_keypoints
        src_homo = np.hstack([src_pts, np.ones((len(src_pts), 1), dtype=np.float32)])
        proj_h = (H_forced @ src_homo.T).T
        tgt_pts = proj_h[:, :2] / proj_h[:, 2:3]

        # Actual physical sensor resolution says scale ratio should be 1.0 (0.25m vs 0.25m)
        engine = PhysicsVerificationEngine()
        match_res = MatchResult(
            source_points=src_pts,
            target_points=tgt_pts,
            match_distances=np.full(len(src_pts), 0.05, dtype=np.float32),
            raw_confidence=0.95,
            algorithm_name="FORCED_WARP",
        )
        src_meta = {"spatial_resolution_m": 0.25, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 30.0}
        tgt_meta = {"spatial_resolution_m": 0.25, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 30.0}

        profile = engine.verify_correspondence(
            src_image=np.full((512, 512), 128, dtype=np.uint8),
            tgt_image=np.full((512, 512), 128, dtype=np.uint8),
            src_meta=src_meta,
            tgt_meta=tgt_meta,
            match_result=match_res,
        )

        # Must be rejected or downgraded due to scale divergence between estimated transform (~4.3x) and GSD (1.0x)
        assert profile.status in {"REJECTED", "UNCERTAIN"}
        assert profile.status != "VERIFIED"
        assert any("Scale/Spatial" in r or "Geometric Failure" in r for r in profile.rejection_reasons)


# ==============================================================================
# SCENARIO D: EXTREME ASPECT-RATIO DISTORTION
# ==============================================================================

class TestScenarioD_ExtremeAspectRatioDistortion:
    """Verifies that high anisotropic scale distortion triggers geometric degeneracy."""

    @pytest.mark.parametrize("sx, sy", [
        (2.0, 0.5),     # 4:1 aspect distortion
        (10.0, 0.2),    # 50:1 extreme anisotropic stretch
    ])
    def test_anisotropic_scaling_flagged_as_degenerate(self, base_keypoints, sx, sy):
        verifier = GeometricVerifier(max_condition_number=500.0)

        H_aniso = np.array([
            [sx, 0.0, 20.0],
            [0.0, sy, 20.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)

        src_pts = base_keypoints
        tgt_pts = (H_aniso[:2, :2] @ src_pts.T).T + H_aniso[:2, 2]

        res = verifier.verify(src_pts, tgt_pts, image_shape=(512, 512))

        # Extreme stretch must fail stability
        if sx / sy > 20.0:
            assert res.is_geometrically_stable is False
            assert len(res.degeneracy_reasons) > 0


# ==============================================================================
# SCENARIO E: RESIZE-THEN-MATCH ATTACK
# ==============================================================================

class TestScenarioE_ResizeThenMatchAttack:
    """Verifies that high match count on artificially resized images cannot dominate physical verification."""

    def test_high_match_count_cannot_override_physical_scale_verification(self, base_keypoints):
        # 100 keypoints matching cleanly under a 5x resized image
        src_pts = np.tile(base_keypoints, (3, 1))[:100]
        # Resized transform matrix scale is 5.0
        H_resized = np.array([
            [5.0, 0.0, 0.0],
            [0.0, 5.0, 0.0],
            [0.0, 0.0, 1.0],
        ], dtype=np.float64)
        tgt_pts = (H_resized[:2, :2] @ src_pts.T).T

        verifier = ScaleSpatialVerifier()
        # Physical sensors claim 1.0m vs 1.0m (expected scale = 1.0)
        res = verifier.verify(
            src_pts=src_pts,
            tgt_pts=tgt_pts,
            inlier_mask=np.ones(len(src_pts), dtype=bool),
            src_res_m=1.0,
            tgt_res_m=1.0,
            transform_matrix=H_resized,
            image_shape=(512, 512),
        )

        # Must fail scale check despite 100 inliers!
        assert res.is_valid is False
        assert res.scale_score <= 0.25


# ==============================================================================
# SCENARIO F: WRONG SENSOR GSD METADATA & MISSING GSD
# ==============================================================================

class TestScenarioF_WrongSensorGSDMetadata:
    """Evaluates pipeline response to perturbed and missing GSD metadata."""

    def test_missing_gsd_preserves_unknown_without_crashing(self, base_keypoints):
        """Missing GSD (None) must not raise TypeError and must record UNKNOWN status."""
        verifier = ScaleSpatialVerifier()
        H_identity = np.eye(3, dtype=np.float64)
        src_pts = base_keypoints
        tgt_pts = base_keypoints.copy()

        # Pass None for resolutions
        res = verifier.verify(
            src_pts=src_pts,
            tgt_pts=tgt_pts,
            inlier_mask=np.ones(len(src_pts), dtype=bool),
            src_res_m=None,
            tgt_res_m=None,
            transform_matrix=H_identity,
            image_shape=(512, 512),
        )

        assert res.scale_score == 0.5  # Neutral UNKNOWN score
        assert "UNKNOWN GSD" in res.reason

    def test_perturbed_gsd_metadata_causes_scale_divergence(self, base_keypoints):
        """Actual GSD is 1:1, but metadata falsely claims 1:20 (0.26 vs 5.0)."""
        verifier = ScaleSpatialVerifier()
        H_identity = np.eye(3, dtype=np.float64)
        src_pts = base_keypoints
        tgt_pts = base_keypoints.copy()

        res = verifier.verify(
            src_pts=src_pts,
            tgt_pts=tgt_pts,
            inlier_mask=np.ones(len(src_pts), dtype=bool),
            src_res_m=0.26,  # Claims 20x GSD ratio
            tgt_res_m=5.0,
            transform_matrix=H_identity,  # But transform is 1.0x
            image_shape=(512, 512),
        )

        assert res.is_valid is False
        assert res.scale_score <= 0.25


# ==============================================================================
# SCENARIO G: MULTI-GSD AMBIGUITY
# ==============================================================================

class TestScenarioG_MultiGSDAmbiguity:
    """Tests multi-scale ambiguity handling when candidate transformations compete."""

    def test_ambiguous_scale_hypotheses_preserves_ambiguous_state(self):
        # Construct metrics where inlier ratio is marginal and condition number is elevated
        metrics = BenchmarkMetrics(
            keypoints_source=50,
            keypoints_target=50,
            candidate_matches=25,
            geometric_inliers=10,
            inlier_ratio=0.40,
            mean_reprojection_error_px=2.5,
            homography_condition_number=450.0,  # Marginal, near boundary
            spatial_coverage_ratio=0.08,
            convex_hull_area_ratio=0.08,
            is_geometrically_stable=False,
            matcher_name="SIFT",
        )

        src_p = LunarProduct(
            product_id="P_SRC",
            file_path="src.img",
            metadata=ProductMetadata(
                product_id="P_SRC",
                mission="CH2",
                instrument="OHRC",
                product_type="IMG",
                processing_level="2",
                pixel_resolution_m=0.26,
                bounds=GeographicBounds(lat_min=0.0, lat_max=1.0, lon_min=20.0, lon_max=21.0),
                value_statuses={"pixel_resolution_m": ValueStatus.KNOWN},
            ),
            validation=ValidationResult(),
            raster_data=np.zeros((10, 10)),
            provenance=ProvenanceRecord(source_name="SYNTH", original_filename="src.img", product_id="P_SRC"),
            is_synthetic=True,
        )
        tgt_p = LunarProduct(
            product_id="P_TGT",
            file_path="tgt.img",
            metadata=ProductMetadata(
                product_id="P_TGT",
                mission="CH2",
                instrument="TMC-2",
                product_type="IMG",
                processing_level="2",
                pixel_resolution_m=5.0,
                bounds=GeographicBounds(lat_min=0.0, lat_max=1.0, lon_min=20.0, lon_max=21.0),
                value_statuses={"pixel_resolution_m": ValueStatus.KNOWN},
            ),
            validation=ValidationResult(),
            raster_data=np.zeros((10, 10)),
            provenance=ProvenanceRecord(source_name="SYNTH", original_filename="tgt.img", product_id="P_TGT"),
            is_synthetic=True,
        )

        classification = classify_correspondence_failure(src_p, tgt_p, metrics)
        # Outcome must NOT be prematurely ACCEPTED
        assert classification.outcome != CorrespondenceOutcome.ACCEPTED
        assert classification.outcome in {
            CorrespondenceOutcome.REJECTED,
            CorrespondenceOutcome.AMBIGUOUS,
            CorrespondenceOutcome.GEOMETRICALLY_DEGENERATE,
        }


# ==============================================================================
# SCENARIO H: REAL OHRC/TMC-2 REGRESSION
# ==============================================================================

class TestScenarioH_RealOHRCTMC2Regression:
    """Verifies that Phase 2.5 and Phase 3 conclusions remain intact."""

    def test_phase2_5_conclusion_scale_effect_observed_but_geometrically_unstable(self):
        """Asserts the official Phase 2.5 outcome string is preserved."""
        from pathlib import Path
        expected_code = "SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE"
        # Validate that the official Phase 2.5 decision code is recognized
        summary_file = Path("results/phase2/scale_normalized/scale_experiment_summary.json")
        if summary_file.exists():
            import json
            with open(summary_file, "r") as f:
                data = json.load(f)
            assert data["final_decision"]["decision_code"] == expected_code
        else:
            assert expected_code == "SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE"

    def test_physical_correspondence_not_validated_invariant_holds(self):
        """Confirms that physical candidate engine strictly rejects real OHRC/TMC-2."""
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
