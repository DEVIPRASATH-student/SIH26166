"""Test Suite for Stage 4.2: Multimodal Evidence Model."""

import pytest
from datetime import datetime

from outgraph.ml.world_model.evidence import (
    EvidenceType,
    EvidenceStatus,
    EvidenceProvenance,
    Evidence,
    EntityEvidenceProfile,
)


def test_evidence_creation_and_provenance():
    prov = EvidenceProvenance(
        source_sensor="SLDEM2015",
        source_product_id="SLDEM2015_512_00N_30N_000_045",
        source_method="BILINEAR_SAMPLING",
        notes="Bilinear elevation sampling at crater center",
    )
    ev = Evidence(
        entity_id="LUNAR-ENT-001",
        observation_id="OBS-DEM-001",
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.SUPPORTED,
        measurement=-1892.4,
        unit="meters",
        uncertainty=15.0,
        provenance=prov,
    )
    assert ev.entity_id == "LUNAR-ENT-001"
    assert ev.evidence_type == EvidenceType.TERRAIN
    assert ev.status == EvidenceStatus.SUPPORTED
    assert ev.measurement == -1892.4
    assert ev.unit == "meters"
    assert ev.uncertainty == 15.0
    assert ev.provenance.source_sensor == "SLDEM2015"
    assert not ev.is_synthetic


def test_evidence_update_in_profile():
    profile = EntityEvidenceProfile(entity_id="LUNAR-ENT-001")
    prov = EvidenceProvenance(source_sensor="OHRC", source_method="SUBMETER_RIM_DETECTION")

    ev1 = Evidence(
        evidence_id="EV-GEOM-1",
        entity_id="LUNAR-ENT-001",
        observation_id="OBS-OHRC-1",
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement={"diameter_m": 120.0},
        provenance=prov,
    )
    profile.add_or_update(ev1)
    assert len(profile.evidence_items) == 1

    # Update with refined measurement
    ev2 = Evidence(
        evidence_id="EV-GEOM-1",
        entity_id="LUNAR-ENT-001",
        observation_id="OBS-OHRC-1",
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement={"diameter_m": 124.5},
        provenance=prov,
    )
    profile.add_or_update(ev2)
    assert len(profile.evidence_items) == 1
    assert profile.evidence_items[0].measurement["diameter_m"] == 124.5


def test_missing_evidence_is_explicit_unknown():
    profile = EntityEvidenceProfile(entity_id="LUNAR-ENT-001")
    # No spectral evidence added
    status = profile.get_status_for_type(EvidenceType.SPECTRAL)
    # Must explicitly return UNKNOWN, not False, not REJECTED
    assert status == EvidenceStatus.UNKNOWN


def test_insufficient_evidence_distinction():
    profile = EntityEvidenceProfile(entity_id="LUNAR-ENT-001")
    prov = EvidenceProvenance(source_sensor="IIRS", source_method="BAND_RATIO")

    ev = Evidence(
        entity_id="LUNAR-ENT-001",
        observation_id="OBS-IIRS-1",
        evidence_type=EvidenceType.SPECTRAL,
        status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
        notes="High noise at 2.8um prevents water ice verification",
        provenance=prov,
    )
    profile.add_or_update(ev)
    status = profile.get_status_for_type(EvidenceType.SPECTRAL)

    assert status == EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert status != EvidenceStatus.UNKNOWN
    assert status != EvidenceStatus.REJECTED
    assert status != EvidenceStatus.CONTRADICTED


def test_contradictory_evidence_detection():
    profile = EntityEvidenceProfile(entity_id="LUNAR-ENT-001")
    prov1 = EvidenceProvenance(source_sensor="OHRC", source_method="VISUAL_RIM")
    prov2 = EvidenceProvenance(source_sensor="TMC-2", source_method="STEREO_ELEVATION")

    ev1 = Evidence(
        entity_id="LUNAR-ENT-001",
        observation_id="OBS-1",
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.SUPPORTED,
        measurement={"rim_elevation_m": -1750.0},
        provenance=prov1,
    )
    ev2 = Evidence(
        entity_id="LUNAR-ENT-001",
        observation_id="OBS-2",
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.CONTRADICTED,
        measurement={"rim_elevation_m": -1950.0},
        notes="200m elevation discrepancy with optical rim shadow",
        provenance=prov2,
    )
    profile.add_or_update(ev1)
    profile.add_or_update(ev2)

    assert profile.has_contradiction() is True
    assert profile.get_status_for_type(EvidenceType.TERRAIN) == EvidenceStatus.CONTRADICTED


def test_uncertainty_interval_preservation():
    prov = EvidenceProvenance(source_sensor="OHRC", source_method="GROUNDGRID")
    ev = Evidence(
        entity_id="LUNAR-ENT-001",
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement={"lat": 0.5542, "lon": 23.4110},
        uncertainty={"bounds_m": [1.4, 3.2], "covariance_trace": 0.08},
        provenance=prov,
    )
    assert isinstance(ev.uncertainty, dict)
    assert ev.uncertainty["bounds_m"] == [1.4, 3.2]


def test_synthetic_evidence_labeling():
    prov = EvidenceProvenance(source_sensor="SYNTHETIC_CRATER_SIMULATOR", source_method="RAY_TRACER")
    ev = Evidence(
        entity_id="LUNAR-ENT-SYNTH",
        evidence_type=EvidenceType.SYNTHETIC,
        status=EvidenceStatus.SUPPORTED,
        is_synthetic=True,
        measurement={"albedo": 0.18},
        provenance=prov,
    )
    assert ev.is_synthetic is True
    assert ev.evidence_type == EvidenceType.SYNTHETIC
