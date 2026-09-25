"""Test Suite for Stages 4.7 & 4.8: Phase 4 World Model Integration & Real-Data Demonstration."""

import pytest

from outgraph.ml.world_model.world_model_engine import WorldModelEngine
from outgraph.ml.world_model.entity import EntityState, AssociationStatus, AssociationType
from outgraph.ml.world_model.evidence import EvidenceType, EvidenceStatus
from outgraph.ml.world_model.knowledge_gap import GapType, GapSeverity
from outgraph.ml.world_model.next_best_observation import InformationGainPotential, SensorFeasibility


def test_real_data_demonstration_execution():
    engine = WorldModelEngine()
    result = engine.run_real_data_demonstration()

    assert result["status"] == "DEMONSTRATION_COMPLETE"
    assert result["final_scientific_determination"] == "PHYSICAL_CORRESPONDENCE_NOT_VALIDATED"
    assert result["has_fabricated_correspondence"] is False

    # Check Entity
    entity = result["entity"]
    assert entity["entity_id"] == "LUNAR-CRATER-MV1"
    assert entity["latitude"] == 0.5542
    assert entity["longitude"] == 23.4110
    assert entity["elevation_m"] == -1892.4

    # Check Associations
    associations = result["associations"]
    assert len(associations) == 2
    ohrc_assoc = [a for a in associations if a["observation_id"] == "OBS-CH2-OHRC-REAL"][0]
    assert ohrc_assoc["status"] == AssociationStatus.SUPPORTED.value
    assert ohrc_assoc["confidence"] == 0.98

    # Check Physical Rejection (Gate 3 Non-Overlap)
    rejected_assoc = result["rejected_association"]
    assert rejected_assoc["observation_id"] == "OBS-CH2-TMC2-REAL"
    assert rejected_assoc["status"] == AssociationStatus.REJECTED.value
    assert "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH" in rejected_assoc["rejection_reason"]
    assert "1773.2m" in rejected_assoc["rejection_reason"]

    # Check Knowledge Gaps
    gaps = result["detected_gaps"]
    assert len(gaps) >= 2
    gap_types = [g["gap_type"] for g in gaps]
    assert GapType.FOOTPRINT_NON_OVERLAP.value in gap_types
    assert GapType.MISSING_SPECTRAL_VALIDATION.value in gap_types

    # Check Recommendations
    recs = result["recommendations"]
    assert len(recs) >= 2
    tmc2_recs = [r for r in recs if r["candidate_sensor"] == "TMC-2"]
    assert len(tmc2_recs) >= 1
    assert "POTENTIALLY_REDUCES_UNCERTAINTY" in tmc2_recs[0]["uncertainty_reduction_basis"]
    assert "WILL_RESOLVE" not in tmc2_recs[0]["uncertainty_reduction_basis"]

    # Check Graph Integration
    assert result["graph_nodes_count"] >= 6
    assert result["graph_edges_count"] >= 4
    # Non-transitivity rule verification:
    assert engine.world_graph.has_valid_correspondence("OBS-CH2-OHRC-REAL", "OBS-CH2-TMC2-REAL") is False
