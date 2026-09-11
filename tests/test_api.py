"""Test Suite for FastAPI Endpoints."""

import pytest
from fastapi.testclient import TestClient
from outgraph.backend.app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "LunarSynapse"


def test_system_health():
    response = client.get("/api/system/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPERATIONAL"
    assert data["database_connected"] is True
    assert data["ml_backends"]["SIFT"] is True


def test_demo_mission_and_flow():
    # 1. Run Complete Demo Mission
    demo_resp = client.post("/api/demo/run")
    assert demo_resp.status_code == 200
    demo_data = demo_resp.json()
    assert demo_data["status"] == "SUCCESS"
    assert demo_data["observations_created"] == 3
    assert demo_data["correspondences_analyzed"] >= 2
    assert demo_data["entities_resolved"] >= 1

    # 2. Query Observations
    obs_resp = client.get("/api/observations")
    assert obs_resp.status_code == 200
    assert len(obs_resp.json()) >= 3

    # 3. Query Entities
    ent_resp = client.get("/api/entities")
    assert ent_resp.status_code == 200
    entities = ent_resp.json()
    assert len(entities) >= 1
    sample_entity_id = entities[0]["entity_id"]

    # 4. Query Entity Detail
    ent_det = client.get(f"/api/entities/{sample_entity_id}")
    assert ent_det.status_code == 200
    assert len(ent_det.json()["hypotheses"]) >= 1

    # 5. Query Graph
    graph_resp = client.get("/api/graph/full")
    assert graph_resp.status_code == 200
    assert len(graph_resp.json()["nodes"]) > 0

    # 6. Query Knowledge Gaps
    gaps_resp = client.get("/api/knowledge-gaps")
    assert gaps_resp.status_code == 200
    assert len(gaps_resp.json()) >= 1

    # 7. Next-Best Observation Recommendation
    rec_resp = client.post(
        "/api/recommendations/next-observation",
        json={"entity_id": sample_entity_id, "scientific_question": "spectral analysis"},
    )
    assert rec_resp.status_code == 200
    assert rec_resp.json()["recommended_sensor"] == "IIRS"


def test_red_team_endpoint():
    resp = client.post("/api/red-team/run")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_deceptive_tests"] >= 4
    assert data["false_positives_prevented"] >= 3
    assert data["prevention_rate"] >= 0.75
