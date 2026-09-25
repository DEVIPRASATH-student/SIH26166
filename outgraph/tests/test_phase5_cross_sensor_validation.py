"""Test Suite for Stage 5.2: Cross-Sensor Entity Lifecycle Validation."""

import pytest

from outgraph.ml.world_model.entity import LunarEntity, EntityResolver, EntityState
from outgraph.ml.world_model.evidence import EntityEvidenceProfile, Evidence, EvidenceType, EvidenceStatus, EvidenceProvenance
from outgraph.ml.world_model.cross_sensor_validator import CrossSensorEntityValidator


def test_case_d_single_observation_not_confirmed():
    """CASE D: Only one observation exists.

    Must remain SUPPORTED, NEVER automatically promoted to CONFIRMED.
    """
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-1",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )

    result = CrossSensorEntityValidator.evaluate_lifecycle(entity)
    assert result.evaluated_case == "CASE_D_SINGLE_OBSERVATION"
    assert result.resulting_state == EntityState.SUPPORTED
    assert result.is_confirmed is False
    assert entity.state == EntityState.SUPPORTED


def test_case_a_compatible_multi_sensor_confirmed():
    """CASE A: Same feature observed by multiple independent sensors with consistent evidence.

    Becomes CONFIRMED.
    """
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    # 1. OHRC observation
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-1",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )
    # 2. Independent sensor (e.g. SLDEM or LROC)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-SLDEM-1",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="SLDEM2015",
    )

    result = CrossSensorEntityValidator.evaluate_lifecycle(entity)
    assert result.evaluated_case == "CASE_A_COMPATIBLE_OVERLAP"
    assert result.resulting_state == EntityState.CONFIRMED
    assert result.is_confirmed is True
    assert entity.state == EntityState.CONFIRMED


def test_same_sensor_multiple_acquisitions_not_multimodal_confirmed():
    """Two acquisitions of the SAME sensor payload (e.g. OHRC T1 and OHRC T2)

    do NOT satisfy multi-modal confirmation on their own.
    """
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-T1",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-T2",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )

    result = CrossSensorEntityValidator.evaluate_lifecycle(entity)
    assert result.evaluated_case == "CASE_A_MONO_SENSOR_MULTIPLE_ACQUISITIONS"
    assert result.resulting_state == EntityState.SUPPORTED
    assert result.is_confirmed is False


def test_case_b_physically_incompatible_rejected():
    """CASE B: Candidate observation rejected due to physical swath non-overlap."""
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-TMC2-DISJOINT",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="TMC-2",
        force_rejection=True,
        rejection_reason="GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH",
    )

    result = CrossSensorEntityValidator.evaluate_lifecycle(entity)
    assert result.evaluated_case == "CASE_B_PHYSICALLY_INCOMPATIBLE"
    assert result.resulting_state == EntityState.REJECTED
    assert result.is_confirmed is False
    assert entity.state == EntityState.REJECTED


def test_case_c_contradictory_evidence_marked_contradicted():
    """CASE C: Two observations have contradictory physical measurements.

    Must transition entity to CONTRADICTED.
    """
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    profile = EntityEvidenceProfile(entity_id=entity.entity_id)

    # 1. OHRC optical measurement
    ev1 = Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.SUPPORTED,
        measurement={"depth_m": 42.0},
        provenance=EvidenceProvenance(source_sensor="OHRC", source_method="SHADOW_LENGTH"),
    )
    # 2. Conflicting measurement
    ev2 = Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.CONTRADICTED,
        measurement={"depth_m": 420.0},
        notes="10x discrepancy with shadow length",
        provenance=EvidenceProvenance(source_sensor="RADAR", source_method="ALTIMETER"),
    )
    profile.add_or_update(ev1)
    profile.add_or_update(ev2)

    result = CrossSensorEntityValidator.evaluate_lifecycle(entity, evidence_profile=profile)
    assert result.evaluated_case == "CASE_C_CONTRADICTORY_EVIDENCE"
    assert result.resulting_state == EntityState.CONTRADICTED
    assert result.is_confirmed is False
    assert entity.state == EntityState.CONTRADICTED
