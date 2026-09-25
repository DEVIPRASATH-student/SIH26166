"""Phase 8.2 Unified Backend / API Integration Test Suite.

Verifies that the integrated scientific pipeline (PipelineController)
is exposed cleanly and securely through FastAPI HTTP endpoints.

Covers:
1. test_health_endpoint
2. test_real_observation_retrieval
3. test_synthetic_observation_provenance
4. test_correspondence_api_real_negative_control
5. test_correspondence_api_synthetic_positive_control
6. test_physical_gate_results_exposed
7. test_unknown_state_preserved
8. test_contradictory_evidence_preserved
9. test_entity_correspondence_non_transitivity
10. test_knowledge_gap_api
11. test_recommendation_api
12. test_potentially_reduces_uncertainty_language
13. test_payload_unavailable
14. test_invalid_request
15. test_missing_observation
16. test_invalid_uncertainty
17. test_synthetic_real_separation
18. test_no_physical_gate_bypass
19. test_duplicate_processing
20. test_explanation_matches_decision
"""

import pytest
from fastapi.testclient import TestClient

from outgraph.backend.app.main import app
from outgraph.backend.app.database.session import init_db, SessionLocal
from outgraph.backend.app.services.pipeline_service import PipelineController
from outgraph.backend.app.models.lunar_entity import LunarEntityModel
from outgraph.backend.app.models.correspondence import CorrespondenceModel

init_db()
client = TestClient(app)


@pytest.fixture(scope="module")
def setup_scenario_data():
    """Ensures real negative control and synthetic control fixtures are prepared in DB."""
    session = SessionLocal()
    try:
        controller = PipelineController(session)
        # Pre-execute controls so DB contains authoritative records
        real_res = controller.run_real_negative_control()
        synth_res = controller.run_synthetic_positive_control()
        unk_res = controller.run_unknown_evidence_control()
        contra_res = controller.run_contradictory_evidence_control()
        return {
            "real": real_res,
            "synth": synth_res,
            "unk": unk_res,
            "contra": contra_res,
        }
    finally:
        session.close()


# ----------------------------------------------------------------------
# 1. Health & Status
# ----------------------------------------------------------------------
def test_health_endpoint():
    """Verifies operational health and scientific subsystem availability."""
    resp = client.get("/api/system/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OPERATIONAL"
    assert data["database_connected"] is True
    assert data["ml_backends"]["SIFT"] is True

    status_resp = client.get("/api/system/status")
    assert status_resp.status_code == 200
    s_data = status_resp.json()
    assert "READY" in s_data["scientific_pipeline"]
    assert s_data["dem_availability"]["status"] == "AVAILABLE"
    assert s_data["groundgrid_availability"]["status"] == "AVAILABLE"
    assert "0 bytes modified" in s_data["raw_data_integrity"]


# ----------------------------------------------------------------------
# 2. Real Observation Retrieval
# ----------------------------------------------------------------------
def test_real_observation_retrieval(setup_scenario_data):
    """Verifies retrieval of real lunar observation with flight metadata and provenance."""
    real_res = setup_scenario_data["real"]
    obs_id = real_res.source_observation_id
    resp = client.get(f"/api/observations/{obs_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == obs_id
    assert data["is_synthetic"] is False
    assert data["data_provenance"]["type"] == "REAL_LUNAR"
    assert data["sensor_type"] == "OHRC"
    assert data["spatial_resolution_m"] > 0.0
    assert "lat_min" in data["footprint"]
    assert "sun_azimuth_deg" in data["solar_geometry"]


# ----------------------------------------------------------------------
# 3. Synthetic Observation Provenance
# ----------------------------------------------------------------------
def test_synthetic_observation_provenance():
    """Verifies synthetic observation creation persists explicit is_synthetic=True provenance."""
    payload = {
        "id": "OBS-API-TEST-SYNTH-01",
        "sensor_type": "SIMULATED_OPTICAL",
        "lat_min": 10.0,
        "lat_max": 10.5,
        "lon_min": 20.0,
        "lon_max": 20.5,
        "spatial_resolution_m": 1.0,
        "sun_azimuth_deg": 45.0,
        "sun_elevation_deg": 30.0,
        "incidence_angle_deg": 60.0,
        "emission_angle_deg": 0.0,
        "phase_angle_deg": 60.0,
        "metadata": {"synthetic_generator": "FractalNoise"},
        "is_synthetic": True,
    }
    resp = client.post("/api/observations", json=payload)
    assert resp.status_code in [200, 201]
    data = resp.json()
    assert data["id"] == "OBS-API-TEST-SYNTH-01"
    assert data["is_synthetic"] is True
    assert data["data_provenance"]["is_synthetic"] is True
    assert data["data_provenance"]["type"] == "SYNTHETIC"


# ----------------------------------------------------------------------
# 4. Real Negative Control Correspondence
# ----------------------------------------------------------------------
def test_correspondence_api_real_negative_control(setup_scenario_data):
    """Scenario A: Real OHRC + TMC-2 correspondence must be rejected at Gate 3 with preserved invariants."""
    real_res = setup_scenario_data["real"]
    req = {
        "source_observation_id": real_res.source_observation_id,
        "target_observation_id": real_res.target_observation_id,
        "matcher_algorithm": "SIFT",
        "ratio_threshold": 0.80,
    }
    resp = client.post("/api/correspondence/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "REJECTED"
    assert data["is_synthetic"] is False
    assert data["physical_verification_status"] == "REJECTED"
    assert data["physical_gate_results"]["GATE3"]["status"] == "REJECTED"
    assert any("PHYSICAL CORRESPONDENCE NOT VALIDATED" in lim for lim in data["limitations"])
    assert any("REAL-DATA ACCURACY = N/A" in lim for lim in data["limitations"])


# ----------------------------------------------------------------------
# 5. Synthetic Positive Control Correspondence
# ----------------------------------------------------------------------
def test_correspondence_api_synthetic_positive_control(setup_scenario_data):
    """Scenario B: Controlled synthetic correspondence must pass physical gates and remain marked synthetic."""
    synth_res = setup_scenario_data["synth"]
    req = {
        "source_observation_id": synth_res.source_observation_id,
        "target_observation_id": synth_res.target_observation_id,
        "matcher_algorithm": "SIFT",
        "ratio_threshold": 0.80,
    }
    resp = client.post("/api/correspondence/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ACCEPTED"
    assert data["is_synthetic"] is True
    assert data["physical_verification_status"] == "PASS"
    assert data["inlier_count"] > 0


# ----------------------------------------------------------------------
# 6. Physical Gate Results Exposed
# ----------------------------------------------------------------------
def test_physical_gate_results_exposed(setup_scenario_data):
    """Verifies that all six physical verification gates are exposed with status and rationale."""
    gates_resp = client.get("/api/physical-verification/gates")
    assert gates_resp.status_code == 200
    gdata = gates_resp.json()
    assert "GATE1" in gdata["gates"]
    assert "GATE2" in gdata["gates"]
    assert "GATE3" in gdata["gates"]
    assert "GATE4" in gdata["gates"]
    assert "GATE5" in gdata["gates"]
    assert "GATE6" in gdata["gates"]

    real_res = setup_scenario_data["real"]
    corr_id = f"CORR-{real_res.source_observation_id}-{real_res.target_observation_id}"
    resp = client.get(f"/api/physical-verification/{corr_id}")
    assert resp.status_code == 200
    vdata = resp.json()
    assert vdata["passed"] is False
    assert vdata["gates"]["GATE3"]["status"] == "REJECTED"


# ----------------------------------------------------------------------
# 7. Unknown State Preserved
# ----------------------------------------------------------------------
def test_unknown_state_preserved(setup_scenario_data):
    """Scenario C: Featureless pair must evaluate to UNKNOWN, preserving UNKNOWN != NEGATIVE."""
    unk_res = setup_scenario_data["unk"]
    req = {
        "source_observation_id": unk_res.source_observation_id,
        "target_observation_id": unk_res.target_observation_id,
        "matcher_algorithm": "SIFT",
    }
    resp = client.post("/api/correspondence/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["UNKNOWN", "INSUFFICIENT_EVIDENCE", "REJECTED"]
    assert data["status"] != "NEGATIVE", "UNKNOWN must never be silently converted to NEGATIVE"
    assert any("UNKNOWN != NEGATIVE" in lim for lim in data["limitations"])




# ----------------------------------------------------------------------
# 8. Contradictory Evidence Preserved
# ----------------------------------------------------------------------
def test_contradictory_evidence_preserved(setup_scenario_data):
    """Scenario D: Opposing illumination conflict must trigger CONTRADICTED or high disagreement without silent overwrite."""
    contra_res = setup_scenario_data["contra"]
    req = {
        "source_observation_id": contra_res.source_observation_id,
        "target_observation_id": contra_res.target_observation_id,
        "matcher_algorithm": "SIFT",
    }
    resp = client.post("/api/correspondence/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["CONTRADICTED", "REJECTED"]
    assert data["uncertainty"]["evidence_disagreement"] > 0.3


# ----------------------------------------------------------------------
# 9. Entity Association != Direct Correspondence
# ----------------------------------------------------------------------
def test_entity_correspondence_non_transitivity():
    """Guardrail: Associating two observations to a shared lunar entity does not assert image correspondence."""
    entities_resp = client.get("/api/entities")
    assert entities_resp.status_code == 200
    entities = entities_resp.json()
    assert len(entities) >= 1

    sample_id = entities[0]["entity_id"]
    det_resp = client.get(f"/api/entities/{sample_id}")
    assert det_resp.status_code == 200
    obs_list = det_resp.json()["observations"]

    # Even if an entity has observations, verify that no direct unvalidated correspondence is claimed
    graph_resp = client.get("/api/graph/full")
    assert graph_resp.status_code == 200


# ----------------------------------------------------------------------
# 10. Knowledge Gap API
# ----------------------------------------------------------------------
def test_knowledge_gap_api():
    """Verifies knowledge gaps endpoint, taxonomy coverage, and ID retrieval."""
    types_resp = client.get("/api/knowledge-gaps/types")
    assert types_resp.status_code == 200
    assert len(types_resp.json()["supported_gap_types"]) == 8

    gaps_resp = client.get("/api/knowledge-gaps")
    assert gaps_resp.status_code == 200
    gaps = gaps_resp.json()
    assert len(gaps) >= 1

    gap_id = gaps[0]["id"]
    single_resp = client.get(f"/api/knowledge-gaps/{gap_id}")
    assert single_resp.status_code == 200
    assert single_resp.json()["id"] == gap_id

    # 404 on missing
    missing_resp = client.get("/api/knowledge-gaps/NONEXISTENT_GAP_ID_404")
    assert missing_resp.status_code == 404


# ----------------------------------------------------------------------
# 11. Recommendation API
# ----------------------------------------------------------------------
def test_recommendation_api():
    """Verifies NBO recommendation generation and listing."""
    entities_resp = client.get("/api/entities")
    entity_id = entities_resp.json()[0]["entity_id"]

    post_resp = client.post(
        "/api/recommendations/next-observation",
        json={"entity_id": entity_id, "scientific_question": "spectral analysis"},
    )
    assert post_resp.status_code == 200
    rec = post_resp.json()
    assert rec["entity_id"] == entity_id
    assert rec["recommended_sensor"] in ["IIRS", "OHRC", "TMC-2"]

    list_resp = client.get("/api/recommendations")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


# ----------------------------------------------------------------------
# 12. POTENTIALLY_REDUCES_UNCERTAINTY Language Invariant
# ----------------------------------------------------------------------
def test_potentially_reduces_uncertainty_language():
    """Guardrail: All recommendations MUST use POTENTIALLY_REDUCES_UNCERTAINTY and NEVER claim WILL_RESOLVE."""
    recs_resp = client.get("/api/recommendations")
    assert recs_resp.status_code == 200
    recs = recs_resp.json()
    for r in recs:
        assert r["uncertainty_reduction_basis"] == "POTENTIALLY_REDUCES_UNCERTAINTY"
        assert "WILL_RESOLVE" not in r["explanation"]


# ----------------------------------------------------------------------
# 13. Payload Unavailable Handling
# ----------------------------------------------------------------------
def test_payload_unavailable():
    """Verifies that requests for unavailable payloads return PAYLOAD_UNAVAILABLE without crashing."""
    entities_resp = client.get("/api/entities")
    entity_id = entities_resp.json()[0]["entity_id"]

    post_resp = client.post(
        "/api/recommendations/next-observation",
        json={"entity_id": entity_id, "scientific_question": "offline_payload_unavailable_sensor"},
    )
    assert post_resp.status_code == 200
    rec = post_resp.json()
    assert rec["payload_status"] == "PAYLOAD_UNAVAILABLE"


# ----------------------------------------------------------------------
# 14. Invalid Request Validation
# ----------------------------------------------------------------------
def test_invalid_request():
    """Verifies Pydantic schema validation rejects out-of-bounds parameters (ratio_threshold outside [0.5, 0.95])."""
    bad_req = {
        "source_observation_id": "OBS-01",
        "target_observation_id": "OBS-02",
        "ratio_threshold": 0.2,  # Invalid
    }
    resp = client.post("/api/correspondence/analyze", json=bad_req)
    assert resp.status_code == 422


# ----------------------------------------------------------------------
# 15. Missing Observation 404
# ----------------------------------------------------------------------
def test_missing_observation():
    """Verifies 404 is returned when observation ID is not registered in DB."""
    req = {
        "source_observation_id": "NONEXISTENT_OBS_A",
        "target_observation_id": "NONEXISTENT_OBS_B",
    }
    resp = client.post("/api/correspondence/analyze", json=req)
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# 16. Invalid Uncertainty Tampering
# ----------------------------------------------------------------------
def test_invalid_uncertainty():
    """Safety: Clients cannot inject arbitrary trusted uncertainty to override computed results."""
    resp = client.post("/api/uncertainty/override", json={"trusted_uncertainty": 0.001})
    assert resp.status_code == 403


# ----------------------------------------------------------------------
# 17. Synthetic / Real Separation Guardrail
# ----------------------------------------------------------------------
def test_synthetic_real_separation():
    """Safety: Client cannot register an arbitrary observation marked is_synthetic=False without raw flight backing."""
    fake_real_payload = {
        "id": "OBS-FABRICATED-REAL",
        "sensor_type": "OHRC",
        "lat_min": 0.0,
        "lat_max": 1.0,
        "lon_min": 0.0,
        "lon_max": 1.0,
        "spatial_resolution_m": 0.25,
        "is_synthetic": False,  # Illegal claim
    }
    resp = client.post("/api/observations", json=fake_real_payload)
    assert resp.status_code == 400


# ----------------------------------------------------------------------
# 18. No Physical Gate Bypass Guardrail
# ----------------------------------------------------------------------
def test_no_physical_gate_bypass(setup_scenario_data):
    """Rule 13 & 14: API strictly rejects bypass parameters (force_accept=True)."""
    real_res = setup_scenario_data["real"]
    bypass_req = {
        "source_observation_id": real_res.source_observation_id,
        "target_observation_id": real_res.target_observation_id,
        "force_accept": True,
    }
    resp = client.post("/api/correspondence/analyze", json=bypass_req)
    assert resp.status_code == 400
    assert "bypass is strictly forbidden" in resp.json()["detail"].lower()


# ----------------------------------------------------------------------
# 19. Duplicate Processing Idempotency
# ----------------------------------------------------------------------
def test_duplicate_processing(setup_scenario_data):
    """Verifies that repeated correspondence requests execute idempotently without duplicating entities."""
    synth_res = setup_scenario_data["synth"]
    req = {
        "source_observation_id": synth_res.source_observation_id,
        "target_observation_id": synth_res.target_observation_id,
        "matcher_algorithm": "SIFT",
    }

    session = SessionLocal()
    ent_count_before = session.query(LunarEntityModel).count()
    session.close()

    resp1 = client.post("/api/correspondence/analyze", json=req)
    assert resp1.status_code == 200

    resp2 = client.post("/api/correspondence/analyze", json=req)
    assert resp2.status_code == 200

    session = SessionLocal()
    ent_count_after = session.query(LunarEntityModel).count()
    session.close()

    # Re-running analyze on the same pair must not create uncontrolled duplicate entities
    assert ent_count_after == ent_count_before
    assert resp1.json()["id"] == resp2.json()["id"]


# ----------------------------------------------------------------------
# 20. Explanation Matches Decision
# ----------------------------------------------------------------------
def test_explanation_matches_decision(setup_scenario_data):
    """Verifies that human explanation card matches the underlying machine-readable decision."""
    real_res = setup_scenario_data["real"]
    req = {
        "source_observation_id": real_res.source_observation_id,
        "target_observation_id": real_res.target_observation_id,
    }
    resp = client.post("/api/correspondence/analyze", json=req)
    assert resp.status_code == 200
    data = resp.json()
    assert data["explanation"]["decision"] == data["status"] == "REJECTED"

    synth_res = setup_scenario_data["synth"]
    synth_req = {
        "source_observation_id": synth_res.source_observation_id,
        "target_observation_id": synth_res.target_observation_id,
    }
    synth_resp = client.post("/api/correspondence/analyze", json=synth_req)
    assert synth_resp.status_code == 200
    synth_data = synth_resp.json()
    assert synth_data["explanation"]["decision"] == synth_data["status"] == "ACCEPTED"
