"""Test Suite for Stage 4.3: Persistent Lunar World Model Knowledge Graph."""

import pytest
import json

from outgraph.ml.world_model.graph import (
    NodeType,
    EdgeRelation,
    WorldGraph,
)


def test_graph_creation_and_node_types():
    wg = WorldGraph()
    wg.add_entity_node("ENT-001", entity_type="crater", latitude=0.5542, longitude=23.4110)
    wg.add_observation_node("OBS-OHRC", sensor_type="OHRC", resolution_m=0.25)
    wg.add_evidence_node("EV-001", evidence_type="TERRAIN", status="SUPPORTED", measurement=-1890.0)
    wg.add_hypothesis_node("HYP-001", property_name="rim_structure", hypothesis_value="Sharp rim")
    wg.add_knowledge_gap_node("GAP-001", gap_type="MISSING_SPECTRAL_EVIDENCE", description="No IIRS data")
    wg.add_recommendation_node("REC-001", candidate_sensor="IIRS", reason="Mineral composition")

    assert len(wg.graph.nodes) == 6
    assert wg.graph.nodes["ENT-001"]["node_type"] == NodeType.ENTITY.value
    assert wg.graph.nodes["OBS-OHRC"]["node_type"] == NodeType.OBSERVATION.value
    assert wg.graph.nodes["EV-001"]["node_type"] == NodeType.EVIDENCE.value
    assert wg.graph.nodes["HYP-001"]["node_type"] == NodeType.HYPOTHESIS.value
    assert wg.graph.nodes["GAP-001"]["node_type"] == NodeType.KNOWLEDGE_GAP.value
    assert wg.graph.nodes["REC-001"]["node_type"] == NodeType.RECOMMENDATION.value


def test_edge_provenance_and_relations():
    wg = WorldGraph()
    wg.add_entity_node("ENT-001")
    wg.add_observation_node("OBS-OHRC", sensor_type="OHRC")

    prov = {"mission": "Chandrayaan-2", "ground_grid_version": "d18"}
    wg.add_relation(
        source_id="OBS-OHRC",
        target_id="ENT-001",
        relation=EdgeRelation.OBSERVES,
        status="SUPPORTED",
        provenance=prov,
        method="GROUND_GRID_GEOREFERENCING",
    )

    edge = wg.graph.get_edge_data("OBS-OHRC", "ENT-001")
    assert edge["relation"] == EdgeRelation.OBSERVES.value
    assert edge["status"] == "SUPPORTED"
    assert edge["provenance"]["mission"] == "Chandrayaan-2"
    assert edge["method"] == "GROUND_GRID_GEOREFERENCING"


def test_non_transitivity_guardrail():
    """CRITICAL TEST:

    OHRC observes Entity E1.
    TMC-2 observes Entity E1 (e.g. from nearby regional context).
    This path does NOT automatically establish an OHRC <-> TMC-2 correspondence!
    """
    wg = WorldGraph()
    wg.add_entity_node("ENT-001")
    wg.add_observation_node("OBS-OHRC", sensor_type="OHRC")
    wg.add_observation_node("OBS-TMC2", sensor_type="TMC-2")

    wg.add_relation("OBS-OHRC", "ENT-001", EdgeRelation.OBSERVES, status="SUPPORTED")
    wg.add_relation("OBS-TMC2", "ENT-001", EdgeRelation.OBSERVES, status="INSUFFICIENT_EVIDENCE")

    # Has path OBS-OHRC -> ENT-001 and OBS-TMC2 -> ENT-001
    # Check guardrail:
    assert wg.has_valid_correspondence("OBS-OHRC", "OBS-TMC2") is False


def test_contradictory_edge_representation():
    wg = WorldGraph()
    wg.add_entity_node("ENT-001")
    wg.add_evidence_node("EV-CONTRADICT", evidence_type="TERRAIN", status="CONTRADICTED")

    wg.add_relation(
        "EV-CONTRADICT",
        "ENT-001",
        relation=EdgeRelation.CONTRADICTED_BY,
        status="CONTRADICTED",
        provenance={"sensor": "TMC-2"},
        method="STEREO_ELEVATION_CHECK",
    )

    edge = wg.graph.get_edge_data("EV-CONTRADICT", "ENT-001")
    assert edge["relation"] == EdgeRelation.CONTRADICTED_BY.value
    assert edge["status"] == "CONTRADICTED"


def test_graph_serialization_and_deterministic_reconstruction():
    wg1 = WorldGraph()
    wg1.add_entity_node("ENT-A", latitude=1.2, longitude=24.5)
    wg1.add_observation_node("OBS-1", sensor_type="OHRC")
    wg1.add_relation("OBS-1", "ENT-A", EdgeRelation.OBSERVES, status="SUPPORTED")

    dict_repr = wg1.to_dict()
    json_repr = wg1.to_json()

    # Reconstruct from dict
    wg2 = WorldGraph.from_dict(dict_repr)
    assert len(wg2.graph.nodes) == len(wg1.graph.nodes)
    assert len(wg2.graph.edges) == len(wg1.graph.edges)
    assert wg2.graph.nodes["ENT-A"]["latitude"] == 1.2

    # Reconstruct from json
    wg3 = WorldGraph.from_json(json_repr)
    assert wg3.to_dict() == dict_repr
