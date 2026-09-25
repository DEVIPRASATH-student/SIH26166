"""Test Suite for Stage 4.5: Knowledge-Gap Detection Engine."""

import pytest

from outgraph.ml.world_model.entity import LunarEntity, EntityResolver, EntityState
from outgraph.ml.world_model.evidence import EntityEvidenceProfile, Evidence, EvidenceType, EvidenceStatus, EvidenceProvenance
from outgraph.ml.world_model.knowledge_gap import (
    GapType,
    GapSeverity,
    GapStatus,
    KnowledgeGap,
    KnowledgeGapDetector,
)


def test_missing_spectral_gap_detection():
    detector = KnowledgeGapDetector()
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )

    gaps = detector.detect_gaps(entity)
    spectral_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_SPECTRAL_VALIDATION]
    assert len(spectral_gaps) == 1
    assert spectral_gaps[0].severity == GapSeverity.HIGH
    assert "IIRS" in spectral_gaps[0].description


def test_missing_terrain_gap_detection():
    detector = KnowledgeGapDetector()
    resolver = EntityResolver()
    # Entity with no elevation specified
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110, elevation_m=None)

    gaps = detector.detect_gaps(entity)
    terrain_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_TERRAIN_VALIDATION]
    assert len(terrain_gaps) == 1
    assert "DEM" in terrain_gaps[0].required_evidence[0]


def test_missing_temporal_observation_gap():
    detector = KnowledgeGapDetector()
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC-1",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
    )

    gaps = detector.detect_gaps(entity)
    temporal_gaps = [g for g in gaps if g.gap_type == GapType.MISSING_TEMPORAL_OBSERVATION]
    assert len(temporal_gaps) == 1


def test_footprint_non_overlap_gap_from_phase3_rejection():
    """CRITICAL TEST:

    Verifies that a Phase 3 physical rejection (GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH)
    is recorded as a FOOTPRINT_NON_OVERLAP knowledge gap rather than a failure of the system.
    """
    detector = KnowledgeGapDetector()
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)

    rejection_event = {
        "source_observation": "OBS-OHRC",
        "target_observation": "OBS-TMC2",
        "rejection_reason": "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH: target scan -140.2 outside swath [0, 80000]",
        "reference_datum_gap_m": 1773.2,
    }

    gaps = detector.detect_gaps(entity, rejection_events=[rejection_event])
    non_overlap_gaps = [g for g in gaps if g.gap_type == GapType.FOOTPRINT_NON_OVERLAP]
    assert len(non_overlap_gaps) == 1
    gap = non_overlap_gaps[0]
    assert gap.severity == GapSeverity.HIGH
    assert gap.blocking_reason == "PHYSICAL_FOOTPRINT_SEPARATION"
    assert "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH" in gap.current_evidence[0]


def test_uncertainty_too_high_gap():
    detector = KnowledgeGapDetector(uncertainty_threshold_m=40.0)
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    entity.uncertainty_m = 65.0  # Exceeds 40m threshold

    gaps = detector.detect_gaps(entity)
    unc_gaps = [g for g in gaps if g.gap_type == GapType.UNCERTAINTY_TOO_HIGH]
    assert len(unc_gaps) == 1
    assert "65.0m" in unc_gaps[0].description
