"""Test Suite for Stage 4.6: Next-Best Observation Engine."""

import pytest

from outgraph.ml.world_model.entity import LunarEntity, EntityResolver
from outgraph.ml.world_model.knowledge_gap import KnowledgeGap, GapType, GapSeverity
from outgraph.ml.world_model.next_best_observation import (
    InformationGainPotential,
    SensorFeasibility,
    NextBestObservation,
    NextBestObservationEngine,
)


def test_footprint_gap_recommendation():
    engine = NextBestObservationEngine()
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    gap = KnowledgeGap(
        gap_id="GAP-001",
        entity_id=entity.entity_id,
        gap_type=GapType.FOOTPRINT_NON_OVERLAP,
        description="Footprints disjoint by 1.77 km",
        severity=GapSeverity.HIGH,
        blocking_reason="PHYSICAL_FOOTPRINT_SEPARATION",
    )

    recs = engine.recommend_for_gap(entity, gap)
    assert len(recs) == 1
    rec = recs[0]
    assert rec.candidate_sensor == "TMC-2"
    assert rec.feasibility == SensorFeasibility.FEASIBLE
    assert rec.information_gain_potential == InformationGainPotential.HIGH_POTENTIAL

    # Crucial scientific check: Uses POTENTIALLY_REDUCES_UNCERTAINTY, NEVER WILL_RESOLVE
    assert "POTENTIALLY_REDUCES_UNCERTAINTY" in rec.uncertainty_reduction_basis
    assert "WILL_RESOLVE" not in rec.uncertainty_reduction_basis


def test_missing_spectral_gap_recommendation():
    engine = NextBestObservationEngine()
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    gap = KnowledgeGap(
        gap_id="GAP-002",
        entity_id=entity.entity_id,
        gap_type=GapType.MISSING_SPECTRAL_VALIDATION,
        description="Lacks mineral composition bands",
        severity=GapSeverity.HIGH,
    )

    recs = engine.recommend_for_gap(entity, gap)
    assert len(recs) == 1
    rec = recs[0]
    assert rec.candidate_sensor == "IIRS"
    assert rec.information_gain_potential == InformationGainPotential.HIGH_POTENTIAL
    assert "POTENTIALLY_REDUCES_UNCERTAINTY" in rec.uncertainty_reduction_basis


def test_unavailable_sensor_feasibility():
    # Catalog where IIRS is offline / unavailable
    engine = NextBestObservationEngine(available_sensors=["OHRC", "TMC-2"])
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    gap = KnowledgeGap(
        gap_id="GAP-003",
        entity_id=entity.entity_id,
        gap_type=GapType.MISSING_SPECTRAL_VALIDATION,
        description="Lacks mineral composition bands",
    )

    recs = engine.recommend_for_gap(entity, gap)
    assert len(recs) == 1
    rec = recs[0]
    assert rec.candidate_sensor == "IIRS"
    assert rec.feasibility == SensorFeasibility.PAYLOAD_UNAVAILABLE


def test_deterministic_generation():
    engine = NextBestObservationEngine()
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    gap = KnowledgeGap(
        gap_id="GAP-004",
        entity_id=entity.entity_id,
        gap_type=GapType.MISSING_TERRAIN_VALIDATION,
        description="Lacks 3D depth",
    )

    recs1 = engine.recommend_for_gap(entity, gap)
    recs2 = engine.recommend_for_gap(entity, gap)
    assert recs1[0].candidate_sensor == recs2[0].candidate_sensor
    assert recs1[0].required_geometry == recs2[0].required_geometry
    assert recs1[0].information_gain_potential == recs2[0].information_gain_potential
