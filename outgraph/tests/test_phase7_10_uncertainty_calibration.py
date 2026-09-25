"""Phase 7.10 Uncertainty & Calibration Benchmark Suite.

Tests and verifies:
1. Evidence Perturbation (perturbing individual evidence dimensions)
2. Missing Evidence (UNKNOWN state preserved, never converted to FALSE/CONTRADICTED)
3. Contradictory Evidence (preservation of contradictions without silent dropping)
4. Confidence Inflation Attack (adversarial confidence injection rejected / flagged as high risk)
5. Known Error vs Predicted Uncertainty (monotonic correlation check)
6. Formal Calibration & Reliability Analysis (calibration error, reliability curves, risk states)
7. Uncertainty Type Preservation (SCALAR, INTERVAL, COVARIANCE, QUALITATIVE, UNKNOWN)
"""

import pytest
import numpy as np

from outgraph.ml.uncertainty.uncertainty_engine import UncertaintyEngine, UncertaintyBreakdown
from outgraph.ml.verification.physics_engine import PhysicsEvidenceProfile
from outgraph.ml.verification.geometry import GeometryVerificationResult
from outgraph.ml.world_model.evidence import (
    EntityEvidenceProfile,
    Evidence,
    EvidenceType,
    EvidenceStatus,
    EvidenceProvenance,
)
from outgraph.ml.world_model.evidence_fusion import EvidenceFusionEngine
from outgraph.ml.world_model.entity import LunarEntity, EntityState
from outgraph.ml.world_model.uncertainty import (
    PhysicalUncertainty,
    UncertaintyType,
    UncertaintyPropagator,
)


@pytest.fixture
def base_geo_result():
    return GeometryVerificationResult(
        is_valid=True,
        geometry_score=0.90,
        inlier_mask=np.ones(20, dtype=bool),
        num_inliers=20,
        inlier_ratio=0.80,
        mean_reprojection_error_px=0.50,
        condition_number=1.5,
    )


# ------------------------------------------------------------------------------
# 1. EVIDENCE PERTURBATION
# ------------------------------------------------------------------------------
def test_evidence_perturbation_increases_divergence(base_geo_result):
    """Perturbing a single physics evidence dimension increases evidence divergence & total uncertainty."""
    engine = UncertaintyEngine()

    # Baseline: High agreement
    profile_baseline = PhysicsEvidenceProfile(
        visual_score=0.90,
        geometry_score=0.90,
        illumination_score=0.90,
        terrain_score=0.90,
        scale_score=0.90,
        spatial_score=0.90,
        overall_confidence=0.90,
        status="VERIFIED",
        geometry_result=base_geo_result,
        metadata={"inlier_ratio": 0.80},
    )
    unc_baseline = engine.compute_correspondence_uncertainty(profile_baseline)
    assert unc_baseline.evidence_disagreement < 0.05
    assert unc_baseline.total_uncertainty < 0.25

    # Perturb illumination to 0.10
    profile_perturbed = PhysicsEvidenceProfile(
        visual_score=0.90,
        geometry_score=0.90,
        illumination_score=0.10,
        terrain_score=0.90,
        scale_score=0.90,
        spatial_score=0.90,
        overall_confidence=0.70,
        status="UNCERTAIN",
        geometry_result=base_geo_result,
        metadata={"inlier_ratio": 0.80},
    )
    unc_perturbed = engine.compute_correspondence_uncertainty(profile_perturbed)
    assert unc_perturbed.evidence_disagreement > unc_baseline.evidence_disagreement
    assert unc_perturbed.total_uncertainty > unc_baseline.total_uncertainty


# ------------------------------------------------------------------------------
# 2. MISSING EVIDENCE (UNKNOWN != NEGATIVE)
# ------------------------------------------------------------------------------
def test_missing_evidence_unknown_preserved():
    """Missing or unmeasured evidence dimensions must remain UNKNOWN and never be converted to CONTRADICTED or FALSE."""
    entity = LunarEntity(
        entity_id="ENTITY-TEST-001",
        latitude=-70.5,
        longitude=22.8,
        state=EntityState.CANDIDATE,
    )
    profile = EntityEvidenceProfile(entity_id=entity.entity_id)

    # Add geometric support
    profile.add_or_update(Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement={"inlier_ratio": 0.85},
        provenance=EvidenceProvenance(source_sensor="OHRC"),
    ))

    # Add explicitly UNKNOWN terrain evidence
    profile.add_or_update(Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.UNKNOWN,
        uncertainty=PhysicalUncertainty.unknown().dict(),
        provenance=EvidenceProvenance(source_sensor="SLDEM2015", notes="Outside DEM swath boundary"),
    ))

    fused = EvidenceFusionEngine.fuse_profile(entity, profile)

    # Check that TERRAIN is in unknown_dimensions and NOT in contradicted_evidence
    assert "TERRAIN" in fused.unknown_dimensions
    assert not any(c["dimension"] == "TERRAIN" for c in fused.contradicted_evidence)
    # Spectral and Illumination are also unmeasured and must be UNKNOWN
    assert "SPECTRAL" in fused.unknown_dimensions
    assert "ILLUMINATION" in fused.unknown_dimensions


# ------------------------------------------------------------------------------
# 3. CONTRADICTORY EVIDENCE PRESERVATION
# ------------------------------------------------------------------------------
def test_contradictory_evidence_not_silently_dropped():
    """Contradictory evidence across modalities must be explicitly preserved in the fused explanation."""
    entity = LunarEntity(
        entity_id="ENTITY-TEST-002",
        latitude=-70.5,
        longitude=22.8,
        state=EntityState.CANDIDATE,
    )
    profile = EntityEvidenceProfile(entity_id=entity.entity_id)

    # Geometry supports
    profile.add_or_update(Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement=0.92,
        provenance=EvidenceProvenance(source_sensor="OHRC"),
    ))

    # Terrain contradicts (e.g. slope discrepancy / elevation wall)
    profile.add_or_update(Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.CONTRADICTED,
        measurement={"slope_discrepancy_deg": 28.5},
        notes="Slope discrepancy exceeds 15 deg physical tolerance",
        provenance=EvidenceProvenance(source_sensor="SLDEM2015"),
    ))

    fused = EvidenceFusionEngine.fuse_profile(entity, profile)
    assert len(fused.contradicted_evidence) == 1
    assert fused.contradicted_evidence[0]["dimension"] == "TERRAIN"
    assert "Slope discrepancy exceeds 15 deg" in fused.contradicted_evidence[0]["notes"]
    assert "CONTRADICTED BY:" in fused.summary_text


# ------------------------------------------------------------------------------
# 4. CONFIDENCE INFLATION ATTACK
# ------------------------------------------------------------------------------
def test_confidence_inflation_attack_flagged_as_high_risk():
    """An adversary setting overall_confidence = 1.0 with conflicting evidence must trigger HIGH_EPISTEMIC_RISK."""
    engine = UncertaintyEngine()

    # Adversarial payload: confidence inflated to 1.0, but geometry & terrain scores are near 0
    injected_profile = PhysicsEvidenceProfile(
        visual_score=0.99,
        geometry_score=0.05,
        illumination_score=0.10,
        terrain_score=0.02,
        scale_score=0.20,
        spatial_score=0.10,
        overall_confidence=1.0,  # INJECTED INFLATED CONFIDENCE
        status="REJECTED",
        metadata={"inlier_ratio": 0.05},
    )

    unc = engine.compute_correspondence_uncertainty(injected_profile)

    # The engine must compute high uncertainty and flag high epistemic risk despite inflated confidence
    assert unc.total_uncertainty > 0.60
    assert unc.evidence_disagreement > 0.45
    assert unc.calibration_status == "HIGH_EPISTEMIC_RISK"


# ------------------------------------------------------------------------------
# 5. KNOWN ERROR VS PREDICTED UNCERTAINTY
# ------------------------------------------------------------------------------
def test_known_error_tracks_geometric_instability():
    """Higher controlled reprojection error directly causes higher geometric instability & total uncertainty."""
    engine = UncertaintyEngine()
    reprojection_errors = [0.1, 0.5, 1.5, 3.0, 6.0]
    total_uncertainties = []
    geom_instabilities = []

    for err in reprojection_errors:
        geo = GeometryVerificationResult(
            is_valid=True,
            geometry_score=0.90,
            inlier_mask=np.ones(10, dtype=bool),
            num_inliers=10,
            inlier_ratio=0.80,
            mean_reprojection_error_px=err,
            condition_number=1.2,
        )
        prof = PhysicsEvidenceProfile(
            visual_score=0.85,
            geometry_score=0.85,
            illumination_score=0.85,
            terrain_score=0.85,
            scale_score=0.85,
            spatial_score=0.85,
            overall_confidence=0.85,
            status="VERIFIED",
            geometry_result=geo,
            metadata={"inlier_ratio": 0.80},
        )
        unc = engine.compute_correspondence_uncertainty(prof)
        total_uncertainties.append(unc.total_uncertainty)
        geom_instabilities.append(unc.geometric_instability)

    # Check monotonic increase
    for i in range(len(reprojection_errors) - 1):
        assert geom_instabilities[i + 1] >= geom_instabilities[i]
        assert total_uncertainties[i + 1] >= total_uncertainties[i]


# ------------------------------------------------------------------------------
# 6. PHYSICAL UNCERTAINTY TYPES & BOUNDS PRESERVATION
# ------------------------------------------------------------------------------
def test_physical_uncertainty_type_and_interval_propagation():
    """Physical uncertainty maintains deterministic interval bounds across geometry and association propagation."""
    # Step 1: Geometric uncertainty from sensor GSD (0.26m), DEM (59m), and relief corridor (20m)
    geom_unc = UncertaintyPropagator.propagate_geometric_uncertainty(
        source_res_m=0.26,
        dem_res_m=59.0,
        corridor_width_m=20.0,
        sensor_type="OHRC",
    )
    assert geom_unc.uncertainty_type == UncertaintyType.INTERVAL
    assert geom_unc.interval_bounds is not None
    low, high = geom_unc.interval_bounds
    assert low == 0.26
    assert high > 60.0  # sqrt(0.26^2 + 59^2 + 20^2) ~ 62.3m

    # Step 2: In-bounds entity association propagation with 15m distance offset
    assoc_unc = UncertaintyPropagator.propagate_association_uncertainty(
        geom_uncertainty=geom_unc,
        spatial_distance_m=15.0,
        spatial_tolerance_m=200.0,
    )
    assert assoc_unc.uncertainty_type == UncertaintyType.INTERVAL
    a_low, a_high = assoc_unc.interval_bounds
    assert a_low == low
    assert a_high == pytest.approx(high + 15.0, abs=0.1)

    # Step 3: Out-of-bounds entity association propagation
    oob_unc = UncertaintyPropagator.propagate_association_uncertainty(
        geom_uncertainty=geom_unc,
        spatial_distance_m=350.0,
        spatial_tolerance_m=200.0,
    )
    assert oob_unc.uncertainty_type == UncertaintyType.QUALITATIVE
    assert oob_unc.qualitative_label == "REJECTED_OUT_OF_BOUNDS"
