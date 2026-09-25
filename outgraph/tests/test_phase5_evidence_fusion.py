"""Test Suite for Stage 5.3: Multimodal Evidence Fusion & Explanation Engine."""

import pytest

from outgraph.ml.world_model.entity import LunarEntity, EntityResolver, EntityState
from outgraph.ml.world_model.evidence import EntityEvidenceProfile, Evidence, EvidenceType, EvidenceStatus, EvidenceProvenance
from outgraph.ml.world_model.evidence_fusion import EvidenceFusionEngine, FusedEvidenceExplanation


def test_evidence_fusion_structure_and_provenance():
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110, initial_state=EntityState.SUPPORTED)
    profile = EntityEvidenceProfile(entity_id=entity.entity_id)

    # 1. OHRC Geometry Evidence
    ev_geom = Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement={"diameter_m": 140.0},
        uncertainty=0.25,
        method="GROUNDGRID_SUBMETER_RIM",
        provenance=EvidenceProvenance(source_sensor="OHRC", source_method="GROUNDGRID"),
    )
    # 2. SLDEM2015 Terrain Evidence
    ev_terr = Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.TERRAIN,
        status=EvidenceStatus.SUPPORTED,
        measurement={"elevation_m": -1892.4},
        uncertainty={"resolution_m": 59.2},
        method="BILINEAR_SAMPLING",
        provenance=EvidenceProvenance(source_sensor="SLDEM2015", source_method="BILINEAR_SAMPLING"),
    )
    # 3. IIRS Spectral - Insufficient
    ev_spec = Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.SPECTRAL,
        status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
        notes="High noise level at 2.8um",
        provenance=EvidenceProvenance(source_sensor="IIRS", source_method="SPECTRAL_CONTINUUM"),
    )
    profile.add_or_update(ev_geom)
    profile.add_or_update(ev_terr)
    profile.add_or_update(ev_spec)

    blocked = ["Calibrated swath non-overlap with TMC-2 (-1.7 km gap)"]
    fused = EvidenceFusionEngine.fuse_profile(entity, profile, blocked_factors=blocked)

    assert isinstance(fused, FusedEvidenceExplanation)
    assert fused.entity_id == entity.entity_id
    assert fused.overall_lifecycle_state == EntityState.SUPPORTED

    # Check supported list
    assert len(fused.supported_evidence) == 2
    sensors = {s["sensor"] for s in fused.supported_evidence}
    assert "OHRC" in sensors
    assert "SLDEM2015" in sensors

    # Check unknown and insufficient dimensions
    assert "SPECTRAL" in fused.insufficient_evidence_dimensions
    assert "TEMPORAL" in fused.unknown_dimensions
    assert "ILLUMINATION" in fused.unknown_dimensions

    # Check blocked factors
    assert len(fused.blocked_factors) == 1
    assert "TMC-2" in fused.blocked_factors[0]

    # Check natural language explanation
    assert "SUPPORTED BY:" in fused.summary_text
    assert "OHRC" in fused.summary_text
    assert "SLDEM2015" in fused.summary_text
    assert "BLOCKED BY:" in fused.summary_text


def test_no_naive_score_averaging():
    """Confirms that evidence fusion does not squash disparate dimensions into a single meaningless score."""
    resolver = EntityResolver()
    entity = resolver.create_entity(latitude=0.5542, longitude=23.4110)
    profile = EntityEvidenceProfile(entity_id=entity.entity_id)

    ev_geom = Evidence(
        entity_id=entity.entity_id,
        evidence_type=EvidenceType.GEOMETRIC,
        status=EvidenceStatus.SUPPORTED,
        measurement={"diameter_m": 120.0},
        provenance=EvidenceProvenance(source_sensor="OHRC"),
    )
    profile.add_or_update(ev_geom)

    fused = EvidenceFusionEngine.fuse_profile(entity, profile)
    # The output retains explicit dictionary mappings of dimensions rather than an arbitrary scalar average
    assert not hasattr(fused, "average_confidence")
    assert len(fused.supported_evidence) == 1
    assert fused.supported_evidence[0]["dimension"] == "GEOMETRIC"
