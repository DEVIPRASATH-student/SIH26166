"""Test Suite for Stage 5.7: Active World Model Self-Evolving Feedback Loop."""

import pytest

from outgraph.ml.world_model.active_loop import ActiveWorldModelLoop
from outgraph.ml.world_model.entity import EntityState
from outgraph.ml.world_model.knowledge_gap import GapStatus, GapType


def test_active_feedback_loop_evolution():
    loop = ActiveWorldModelLoop()

    # 1. Initial Pass
    init_res = loop.execute_initial_pass(entity_id="LUNAR-TEST-LOOP-01")
    assert init_res["entity_state"] == EntityState.SUPPORTED.value
    assert GapType.MISSING_TERRAIN_VALIDATION.value in init_res["active_gaps"]
    assert "TMC-2" in init_res["recommendations"] or "SLDEM2015" in init_res["recommendations"]

    # Check unconfirmed before follow-up
    assert loop.entity.state == EntityState.SUPPORTED

    # 2. Ingest Recommended Follow-up Observation (SLDEM2015 altimetry)
    follow_res = loop.ingest_followup_observation(
        followup_obs_id="OBS-SLDEM-ACTUAL",
        sensor_type="SLDEM2015",
        measured_elevation_m=-1892.4,
        is_synthetic=False,
    )
    assert follow_res["is_confirmed"] is True
    assert follow_res["updated_entity_state"] == EntityState.CONFIRMED.value
    assert follow_res["association_count"] == 2
    assert follow_res["resolved_gap_count"] >= 1

    # Check that the terrain gap was marked RESOLVED
    terrain_gap = [g for g in loop.gaps if g.gap_type == GapType.MISSING_TERRAIN_VALIDATION][0]
    assert terrain_gap.status == GapStatus.RESOLVED

    # Check provenance preservation
    assert len(loop.execution_log) == 2
    assert loop.execution_log[0]["stage"] == "INITIAL_PASS_COMPLETE"
    assert loop.execution_log[1]["stage"] == "FOLLOWUP_INGESTED"

    # Check graph update
    assert "OBS-SLDEM-ACTUAL" in loop.world_graph.graph.nodes
    assert loop.world_graph.graph.has_edge("OBS-SLDEM-ACTUAL", "LUNAR-TEST-LOOP-01")
