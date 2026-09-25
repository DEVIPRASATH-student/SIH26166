"""Test Suite for Stage 5.9: World Model Scientific Explainability Engine."""

import pytest

from outgraph.ml.world_model.entity import LunarEntity, EntityResolver, EntityState
from outgraph.ml.world_model.evidence import EntityEvidenceProfile, Evidence, EvidenceType, EvidenceStatus, EvidenceProvenance
from outgraph.ml.world_model.knowledge_gap import KnowledgeGap, GapType, GapSeverity
from outgraph.ml.world_model.next_best_observation import NextBestObservation, SensorFeasibility, InformationGainPotential
from outgraph.ml.world_model.explainability import ExplainabilityEngine, EntityExplanationCard


def test_entity_explanation_card_generation():
    resolver = EntityResolver()
    entity = resolver.create_entity(
        entity_id="LUNAR-CRATER-EXP-01",
        latitude=0.5542,
        longitude=23.4110,
        elevation_m=-1892.4,
        initial_state=EntityState.SUPPORTED,
    )

    # Add OHRC association
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-OHRC",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="OHRC",
        confidence=0.98,
    )
    # Add TMC-2 rejected association
    resolver.associate_observation(
        entity_id=entity.entity_id,
        observation_id="OBS-TMC2",
        obs_lat=0.5542,
        obs_lon=23.4110,
        sensor_type="TMC-2",
        force_rejection=True,
        rejection_reason="GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH (-1.7 km gap)",
    )

    profile = EntityEvidenceProfile(entity_id=entity.entity_id)
    profile.add_or_update(
        Evidence(
            entity_id=entity.entity_id,
            evidence_type=EvidenceType.GEOMETRIC,
            status=EvidenceStatus.SUPPORTED,
            method="SUBMETER_RIM_DELINEATION",
            provenance=EvidenceProvenance(source_sensor="OHRC"),
        )
    )

    gap = KnowledgeGap(
        gap_id="GAP-01",
        entity_id=entity.entity_id,
        gap_type=GapType.FOOTPRINT_NON_OVERLAP,
        description="Footprints disjoint",
        severity=GapSeverity.HIGH,
    )

    rec = NextBestObservation(
        target_entity_id=entity.entity_id,
        knowledge_gap_id="GAP-01",
        gap_type=GapType.FOOTPRINT_NON_OVERLAP,
        candidate_sensor="TMC-2",
        reason="Bridge swath gap",
        required_geometry="Adjacent track shifted by 2km west",
        expected_evidence_type=EvidenceType.PHYSICAL,
        feasibility=SensorFeasibility.FEASIBLE,
        uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY by establishing physical spatial overlap",
        information_gain_potential=InformationGainPotential.HIGH_POTENTIAL,
    )

    card = ExplainabilityEngine.generate_card(
        entity=entity,
        evidence_profile=profile,
        gaps=[gap],
        recommendations=[rec],
    )

    assert isinstance(card, EntityExplanationCard)
    assert card.entity_id == "LUNAR-CRATER-EXP-01"
    assert card.lifecycle_state == EntityState.SUPPORTED.value
    assert len(card.supported_evidence) >= 1
    assert any("OHRC" in s for s in card.supported_evidence)
    assert len(card.blocked_factors) >= 1
    assert "GATE3" in card.blocked_factors[0]
    assert len(card.active_knowledge_gaps) >= 1
    assert len(card.recommended_next_observations) >= 1
    assert "POTENTIALLY_REDUCES_UNCERTAINTY" in card.recommended_next_observations[0]
    assert "EXPLANATION CARD" in card.full_text_report
