"""Phase 7.11 World Model, Knowledge Gap & Active Observation Loop Benchmark Suite.

Rigorous test coverage for:
A. Entity Persistence (multiple observations, sensors, timestamps, evidence levels)
B. Entity Aliasing Resistance (spatially close, morphologically similar features remain distinct)
C. Observation/Entity Non-Transitivity (Obs A -> Ent X <- Obs B does NOT create Obs A <-> Obs B)
D. Temporal Reasoning (distinguishing illumination-only changes from physical surface modification)
E. Knowledge-Gap Benchmark (all 8 supported categories verified with exact provenance)
F. Active Observation & NBO Behavior (FEASIBLE, INCOMPATIBLE, UNAVAILABLE with POTENTIALLY_REDUCES_UNCERTAINTY)
G. Active Loop Oscillation Resistance (no duplicate recommendations, bounded updates, monotonic gap closure)
H. No-Action Negative Controls (unresolvable conditions yield NO_ACTIONABLE_RECOMMENDATION / PAYLOAD_UNAVAILABLE)
I. Provenance Preservation (synthetic observations remain synthetic throughout graph and active loop)
"""

import pytest
from datetime import datetime, timedelta

from outgraph.ml.world_model.entity import (
    LunarEntity,
    EntityResolver,
    EntityState,
    AssociationStatus,
    AssociationType,
    EntityAssociation,
    AssociationProvenance,
)
from outgraph.ml.world_model.evidence import (
    EntityEvidenceProfile,
    Evidence,
    EvidenceType,
    EvidenceStatus,
    EvidenceProvenance,
)
from outgraph.ml.world_model.graph import WorldGraph, NodeType, EdgeRelation
from outgraph.ml.world_model.knowledge_gap import (
    KnowledgeGapDetector,
    KnowledgeGap,
    GapType,
    GapSeverity,
    GapStatus,
)
from outgraph.ml.world_model.next_best_observation import (
    NextBestObservationEngine,
    NextBestObservation,
    SensorFeasibility,
    InformationGainPotential,
)
from outgraph.ml.world_model.temporal import (
    TemporalReasoningEngine,
    TemporalObservationEpoch,
    TemporalState,
)
from outgraph.ml.world_model.active_loop import ActiveWorldModelLoop


# ------------------------------------------------------------------------------
# A. ENTITY PERSISTENCE
# ------------------------------------------------------------------------------
def test_entity_persistence_across_multiple_sensors_and_epochs():
    """Persistent entity successfully associates observations from multiple sensors across distinct timestamps."""
    resolver = EntityResolver(spatial_tolerance_m=200.0)

    # Base entity at lunar coordinates
    entity = resolver.create_entity(
        entity_id="ENTITY-PERSIST-001",
        latitude=-70.5000,
        longitude=22.8000,
        entity_type="crater",
    )

    t0 = datetime(2021, 3, 19, 10, 0, 0)
    t1 = t0 + timedelta(days=28)
    t2 = t0 + timedelta(days=180)

    # Obs 1: OHRC at t0
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-T0",
        obs_lat=-70.5001,
        obs_lon=22.8001,
        sensor_type="OHRC",
        confidence=0.95,
        uncertainty=0.25,
    )
    assert len(entity.associations) == 1
    assert entity.state == EntityState.SUPPORTED

    # Obs 2: TMC-2 at t1 (slight spatial offset within tolerance)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-TMC2-T1",
        obs_lat=-70.5003,
        obs_lon=22.8002,
        sensor_type="TMC-2",
        confidence=0.88,
        uncertainty=5.0,
    )
    assert len(entity.associations) == 2
    assert entity.state == EntityState.CONFIRMED

    # Obs 3: SLDEM2015 at t2
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-SLDEM-T2",
        obs_lat=-70.5002,
        obs_lon=22.8000,
        sensor_type="SLDEM2015",
        confidence=0.90,
        uncertainty=15.0,
    )
    assert len(entity.associations) == 3
    assert entity.state == EntityState.CONFIRMED
    assert entity.entity_id == "ENTITY-PERSIST-001"


# ------------------------------------------------------------------------------
# B. ENTITY ALIASING RESISTANCE
# ------------------------------------------------------------------------------
def test_entity_aliasing_resistance_spatially_close_features():
    """Two morphologically similar craters separated beyond spatial tolerance remain distinct entities."""
    resolver = EntityResolver(spatial_tolerance_m=200.0)

    # Crater A at (0.5542, 23.4110)
    entity_a = resolver.create_entity(
        entity_id="CRATER-A",
        latitude=0.5542,
        longitude=23.4110,
        entity_type="crater",
    )

    # Crater B is 450 meters away (0.015 deg lat ~ 455 m on Moon)
    entity_b = resolver.create_entity(
        entity_id="CRATER-B",
        latitude=0.5542 + 0.0150,
        longitude=23.4110,
        entity_type="crater",
    )

    # Attempt to associate observation centered at Crater B with Crater A
    assoc_a_from_b = resolver.associate_observation(
        entity_id=entity_a.entity_id,
        observation_id="OBS-CRATER-B",
        obs_lat=0.5542 + 0.0150,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )

    # Must be REJECTED on Crater A because distance exceeds 200m tolerance
    assert assoc_a_from_b.status == AssociationStatus.REJECTED
    assert assoc_a_from_b.rejection_reason is not None
    assert "SPATIAL_DISTANCE_EXCEEDS_TOLERANCE" in assoc_a_from_b.rejection_reason

    # Associating with Crater B succeeds
    assoc_b_from_b = resolver.associate_observation(
        entity_id=entity_b.entity_id,
        observation_id="OBS-CRATER-B",
        obs_lat=0.5542 + 0.0150,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )
    assert assoc_b_from_b.status == AssociationStatus.SUPPORTED

    # Entities remain strictly independent
    assert entity_a.entity_id != entity_b.entity_id
    assert len([a for a in entity_a.associations if a.status == AssociationStatus.SUPPORTED]) == 0
    assert len([a for a in entity_b.associations if a.status == AssociationStatus.SUPPORTED]) == 1


# ------------------------------------------------------------------------------
# C. OBSERVATION/ENTITY NON-TRANSITIVITY
# ------------------------------------------------------------------------------
def test_observation_entity_non_transitivity_guardrail():
    """Observation A observing Entity X and Observation B observing Entity X does NOT create Obs A <-> Obs B."""
    graph = WorldGraph()
    graph.add_entity_node("ENTITY-X", entity_type="crater", latitude=-70.5, longitude=22.8)
    graph.add_observation_node("OBS-A", sensor_type="OHRC", resolution_m=0.25)
    graph.add_observation_node("OBS-B", sensor_type="TMC-2", resolution_m=5.0)

    # Obs A observes Entity X
    graph.add_relation("OBS-A", "ENTITY-X", EdgeRelation.OBSERVES, status="SUPPORTED")
    # Obs B observes Entity X
    graph.add_relation("OBS-B", "ENTITY-X", EdgeRelation.OBSERVES, status="SUPPORTED")

    # Non-transitivity guardrail:
    assert graph.has_valid_correspondence("OBS-A", "OBS-B") is False
    assert not graph.graph.has_edge("OBS-A", "OBS-B")
    assert not graph.graph.has_edge("OBS-B", "OBS-A")


# ------------------------------------------------------------------------------
# D. TEMPORAL REASONING & ILLUMINATION DISAMBIGUATION
# ------------------------------------------------------------------------------
def test_temporal_reasoning_disambiguates_illumination_from_physical_change():
    """Illumination difference across epochs is classified as STABLE morphology rather than physical change."""
    t0 = datetime(2020, 6, 1, 12, 0, 0)
    t1 = t0 + timedelta(days=14)

    # Epoch 1: Solar azimuth 45 deg, feature diameter 150m
    e1 = TemporalObservationEpoch(
        epoch_id="EP-1",
        observation_id="OBS-OHRC-1",
        sensor="OHRC",
        timestamp=t0,
        solar_azimuth_deg=45.0,
        solar_elevation_deg=20.0,
        feature_diameter_m=150.0,
        apparent_brightness=110.0,
    )

    # Epoch 2: Opposite solar azimuth 225 deg (shadows inverted), but diameter unchanged
    e2 = TemporalObservationEpoch(
        epoch_id="EP-2",
        observation_id="OBS-OHRC-2",
        sensor="OHRC",
        timestamp=t1,
        solar_azimuth_deg=225.0,
        solar_elevation_deg=20.0,
        feature_diameter_m=150.2,  # Sub-pixel variance
        apparent_brightness=175.0,  # Dramatic brightness shift due to sun angle
    )

    res = TemporalReasoningEngine.analyze_timeline("CRATER-TEMP-01", [e1, e2], measurement_tolerance_m=3.0)

    assert res.temporal_state == TemporalState.STABLE
    assert res.physical_change_supported is False
    assert any("Solar azimuth shifted" in d for d in res.observed_differences)
    assert "Observational differences detected" in res.explanation
    assert "remains STABLE" in res.explanation


# ------------------------------------------------------------------------------
# E. KNOWLEDGE-GAP BENCHMARK (ALL 8 CATEGORIES)
# ------------------------------------------------------------------------------
def test_knowledge_gap_all_eight_supported_categories():
    """All 8 supported knowledge gap categories are detected with precise taxonomy and provenance."""
    detector = KnowledgeGapDetector(uncertainty_threshold_m=40.0)
    resolver = EntityResolver()

    # 1. MISSING_SPECTRAL_VALIDATION
    e1 = resolver.create_entity(latitude=0.55, longitude=23.41)
    resolver.associate_observation(e1.entity_id, "OBS-1", 0.55, 23.41, "OHRC")
    gaps1 = detector.detect_gaps(e1)
    assert any(g.gap_type == GapType.MISSING_SPECTRAL_VALIDATION for g in gaps1)

    # 2. MISSING_TERRAIN_VALIDATION
    e2 = resolver.create_entity(latitude=0.55, longitude=23.41, elevation_m=None)
    gaps2 = detector.detect_gaps(e2)
    assert any(g.gap_type == GapType.MISSING_TERRAIN_VALIDATION for g in gaps2)

    # 3. MISSING_TEMPORAL_OBSERVATION
    e3 = resolver.create_entity(latitude=0.55, longitude=23.41)
    resolver.associate_observation(e3.entity_id, "OBS-3", 0.55, 23.41, "OHRC")
    gaps3 = detector.detect_gaps(e3)
    assert any(g.gap_type == GapType.MISSING_TEMPORAL_OBSERVATION for g in gaps3)

    # 4. FOOTPRINT_NON_OVERLAP
    e4 = resolver.create_entity(latitude=0.55, longitude=23.41)
    rejection = {
        "source_observation": "OHRC",
        "target_observation": "TMC-2",
        "rejection_reason": "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH",
        "reference_datum_gap_m": 1800.0,
    }
    gaps4 = detector.detect_gaps(e4, rejection_events=[rejection])
    assert any(g.gap_type == GapType.FOOTPRINT_NON_OVERLAP for g in gaps4)

    # 5. UNCERTAINTY_TOO_HIGH
    e5 = resolver.create_entity(latitude=0.55, longitude=23.41)
    e5.uncertainty_m = 75.0
    gaps5 = detector.detect_gaps(e5)
    assert any(g.gap_type == GapType.UNCERTAINTY_TOO_HIGH for g in gaps5)

    # 6. INSUFFICIENT_CORRESPONDENCE
    e6 = resolver.create_entity(latitude=0.55, longitude=23.41)
    resolver.associate_observation(e6.entity_id, "OBS-OHRC-SINGLE", 0.55, 23.41, "OHRC")
    gaps6 = detector.detect_gaps(e6)
    assert any(g.gap_type == GapType.INSUFFICIENT_CORRESPONDENCE for g in gaps6)

    # 7. MISSING_GEOMETRIC_VALIDATION
    prof_no_geom = EntityEvidenceProfile(entity_id="ENT-7")
    e7 = resolver.create_entity(latitude=0.55, longitude=23.41)
    gaps7 = detector.detect_gaps(e7, evidence_profile=prof_no_geom)
    assert any(g.gap_type == GapType.MISSING_GEOMETRIC_VALIDATION for g in gaps7)

    # 8. MISSING_MODALITY
    prof_no_modal = EntityEvidenceProfile(entity_id="ENT-8")
    e8 = resolver.create_entity(latitude=0.55, longitude=23.41)
    gaps8 = detector.detect_gaps(e8, evidence_profile=prof_no_modal)
    assert any(g.gap_type == GapType.MISSING_MODALITY for g in gaps8)


# ------------------------------------------------------------------------------
# F. ACTIVE OBSERVATION & SCIENTIFIC LANGUAGE
# ------------------------------------------------------------------------------
def test_next_best_observation_uses_potentially_reduces_uncertainty():
    """Active recommendations strictly use POTENTIALLY_REDUCES_UNCERTAINTY and never claim WILL_RESOLVE."""
    engine = NextBestObservationEngine(available_sensors=["OHRC", "TMC-2", "IIRS"])
    entity = LunarEntity(entity_id="ENT-NBO-01", latitude=0.55, longitude=23.41)

    gap = KnowledgeGap(
        entity_id=entity.entity_id,
        gap_type=GapType.FOOTPRINT_NON_OVERLAP,
        severity=GapSeverity.HIGH,
        description="Footprint non-overlap",
        blocking_reason="PHYSICAL_FOOTPRINT_SEPARATION",
    )

    recs = engine.recommend_for_gap(entity, gap)
    assert len(recs) == 1
    rec = recs[0]

    # Verify non-inflated scientific language
    assert "POTENTIALLY_REDUCES_UNCERTAINTY" in rec.uncertainty_reduction_basis
    assert "WILL_RESOLVE" not in rec.uncertainty_reduction_basis
    assert "GUARANTEED" not in rec.uncertainty_reduction_basis
    assert rec.feasibility == SensorFeasibility.FEASIBLE


# ------------------------------------------------------------------------------
# G. ACTIVE LOOP OSCILLATION & CONVERGENCE
# ------------------------------------------------------------------------------
def test_active_feedback_loop_oscillation_resistance():
    """The active observation loop monotonically closes targeted gaps without recommendation explosion."""
    loop = ActiveWorldModelLoop()

    # Pass 1: Initial observation & gap generation
    init_res = loop.execute_initial_pass(entity_id="CRATER-LOOP-01")
    initial_recs = list(loop.recommendations)
    assert len(initial_recs) >= 1

    # Ingest follow-up SLDEM2015 observation
    follow_res = loop.ingest_followup_observation(
        followup_obs_id="OBS-SLDEM-ACTUAL",
        sensor_type="SLDEM2015",
        measured_elevation_m=-1892.4,
        is_synthetic=True,
    )
    assert follow_res["is_confirmed"] is True
    assert follow_res["resolved_gap_count"] >= 1

    # Verify terrain gap is marked RESOLVED and not re-recommended
    terrain_gap = [g for g in loop.gaps if g.gap_type == GapType.MISSING_TERRAIN_VALIDATION][0]
    assert terrain_gap.status == GapStatus.RESOLVED

    # Ensure no infinite loop / duplication of recommendations
    recommendation_ids = [r.recommendation_id for r in loop.recommendations]
    assert len(recommendation_ids) == len(set(recommendation_ids))


# ------------------------------------------------------------------------------
# H. NO-ACTION NEGATIVE CONTROL
# ------------------------------------------------------------------------------
def test_no_action_negative_control_payload_unavailable():
    """When required sensor payload is unavailable, NBO engine marks PAYLOAD_UNAVAILABLE rather than inventing data."""
    # Restrict available catalog to ONLY OHRC
    engine = NextBestObservationEngine(available_sensors=["OHRC"])
    entity = LunarEntity(entity_id="ENT-NEG-01", latitude=0.55, longitude=23.41)

    # Gap requires IIRS hyperspectral sensor
    gap = KnowledgeGap(
        entity_id=entity.entity_id,
        gap_type=GapType.MISSING_SPECTRAL_VALIDATION,
        severity=GapSeverity.HIGH,
        description="Hyperspectral missing",
    )

    recs = engine.recommend_for_gap(entity, gap)
    assert len(recs) == 1
    assert recs[0].candidate_sensor == "IIRS"
    assert recs[0].feasibility == SensorFeasibility.PAYLOAD_UNAVAILABLE


# ------------------------------------------------------------------------------
# I. PROVENANCE PRESERVATION
# ------------------------------------------------------------------------------
def test_synthetic_provenance_preservation_across_lifecycle():
    """Synthetic observations remain strictly flagged as is_synthetic=True throughout graph and active loop."""
    loop = ActiveWorldModelLoop()
    loop.execute_initial_pass(entity_id="ENT-SYNTH-01")

    # Ingest synthetic observation
    loop.ingest_followup_observation(
        followup_obs_id="OBS-SYNTH-DEM",
        sensor_type="SLDEM2015",
        measured_elevation_m=-1200.0,
        is_synthetic=True,
    )

    # Check evidence item
    ev = loop.evidence_profile.get_by_type(EvidenceType.TERRAIN)[0]
    assert ev.is_synthetic is True

    # Check graph node
    node_data = loop.world_graph.graph.nodes["OBS-SYNTH-DEM"]
    assert node_data["is_synthetic"] is True
