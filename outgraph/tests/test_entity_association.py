"""Test Suite for Stage 4.1: Observation -> Entity Association Engine."""

import pytest
from datetime import datetime

from outgraph.ml.world_model.entity import (
    EntityState,
    AssociationType,
    AssociationStatus,
    EntityAssociation,
    LunarEntity,
    EntityResolver,
)


def test_valid_entity_creation():
    resolver = EntityResolver(spatial_tolerance_m=250.0)
    entity = resolver.create_entity(
        latitude=0.5542,
        longitude=23.4110,
        entity_type="crater",
        spatial_extent_m=120.0,
        elevation_m=-1892.4,
        entity_id="LUNAR-TEST-001",
    )
    assert entity.entity_id == "LUNAR-TEST-001"
    assert entity.entity_type == "crater"
    assert entity.state == EntityState.CANDIDATE
    assert entity.latitude == 0.5542
    assert entity.longitude == 23.4110
    assert entity.elevation_m == -1892.4
    assert len(entity.associations) == 0


def test_valid_observation_association():
    resolver = EntityResolver(spatial_tolerance_m=200.0)
    entity = resolver.create_entity(
        latitude=0.5542,
        longitude=23.4110,
        entity_type="crater",
    )
    # Associate observation 50m away
    # 0.0001 deg latitude is approx 3.03 m on Moon
    assoc = resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-001",
        obs_lat=0.5543,
        obs_lon=23.4110,
        sensor_type="OHRC",
        product_id="ch2_ohr_ncp_20210319",
        confidence=0.95,
        uncertainty=0.05,
    )
    assert assoc.status == AssociationStatus.SUPPORTED
    assert assoc.association_type == AssociationType.GEOMETRIC
    assert assoc.geometric_distance_m is not None
    assert assoc.geometric_distance_m < 200.0
    assert entity.state == EntityState.SUPPORTED
    assert len(entity.associations) == 1


def test_duplicate_association_handling():
    resolver = EntityResolver(spatial_tolerance_m=200.0)
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    # First association
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-001",
        obs_lat=0.5543,
        obs_lon=23.4110,
        sensor_type="OHRC",
        confidence=0.85,
    )
    assert len(entity.associations) == 1

    # Second association with updated confidence
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-001",
        obs_lat=0.5543,
        obs_lon=23.4110,
        sensor_type="OHRC",
        confidence=0.96,
    )
    assert len(entity.associations) == 1
    assert entity.associations[0].confidence == 0.96


def test_rejected_association_due_to_distance():
    resolver = EntityResolver(spatial_tolerance_m=200.0)
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    # Observation is ~1.7 km away (similar to Stage 2 OHRC/TMC-2 gap)
    # 0.05 deg latitude is ~1.5 km
    assoc = resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-TMC2-001",
        obs_lat=0.6042,
        obs_lon=23.4110,
        sensor_type="TMC-2",
    )
    assert assoc.status == AssociationStatus.REJECTED
    assert assoc.association_type == AssociationType.REJECTED
    assert assoc.geometric_distance_m > 1000.0
    assert "SPATIAL_DISTANCE_EXCEEDS_TOLERANCE" in assoc.rejection_reason
    assert entity.state == EntityState.REJECTED


def test_forced_rejection_with_reason():
    resolver = EntityResolver(spatial_tolerance_m=200.0)
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    assoc = resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-TMC2-DISJOINT",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="TMC-2",
        force_rejection=True,
        rejection_reason="GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH",
    )
    assert assoc.status == AssociationStatus.REJECTED
    assert assoc.rejection_reason == "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH"


def test_provenance_preservation():
    resolver = EntityResolver(spatial_tolerance_m=200.0)
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    assoc = resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-PROV",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
        product_id="ch2_ohr_product_123",
        notes="High-precision tie point from Stage 1 GroundGrid",
    )
    prov = assoc.provenance
    assert prov.source_observation_id == "OBS-OHRC-PROV"
    assert prov.source_sensor == "OHRC"
    assert prov.source_product_id == "ch2_ohr_product_123"
    assert prov.notes == "High-precision tie point from Stage 1 GroundGrid"
    assert isinstance(prov.timestamp, datetime)


def test_multimodal_confirmation_state():
    resolver = EntityResolver(spatial_tolerance_m=200.0)
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    # 1. OHRC association
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-001",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )
    assert entity.state == EntityState.SUPPORTED

    # 2. Second valid observation (e.g. LROC NAC or overlapping observation)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-LROC-001",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="LROC_NAC",
    )
    assert entity.state == EntityState.CONFIRMED
