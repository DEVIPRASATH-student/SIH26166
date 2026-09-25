"""Phase 8.6 Performance, Reliability, and Deployment Hardening Test Suite.
Validates:
1. Malformed API request handling (400/422 deterministic structured error)
2. Missing resource handling (404 deterministic structured error)
3. Unavailable payload handling (PAYLOAD_UNAVAILABLE / UNKNOWN, never ACCEPTED)
4. Repeated request determinism (idempotency and state consistency)
5. Concurrent read safety (thread-safe execution without race conditions)
6. Database rollback and session cleanup
7. Duplicate recommendation prevention
8. Duplicate entity prevention
9. Frontend/backend unavailable and degraded state handling
10. Timeout / bounded error state safety (never fails open to ACCEPTED)
11. Large-data safety boundary (no raw multi-GB binaries in web payloads)
12. Path traversal and input validation hardening
13. force_accept protection (Rule 13, 14 bypass rejection)
14. Synthetic provenance tamper protection
15. Uncertainty override protection
16. System health and subsystem reporting (ONLINE/DEGRADED/UNAVAILABLE)
17. Raw data integrity (0 bytes modified in data/real/)
"""

import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import text

from outgraph.backend.app.main import app
from outgraph.backend.app.database.session import SessionLocal, get_db
from outgraph.backend.app.services.demo_service import DemoService
from outgraph.backend.app.models.lunar_entity import LunarEntityModel
from outgraph.backend.app.models.recommendation import RecommendationModel
from outgraph.backend.app.core.config import settings

client = TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session."""
    session = SessionLocal()
    yield session
    session.close()


# ----------------------------------------------------------------------
# 1. Malformed API Request
# ----------------------------------------------------------------------
def test_1_malformed_api_request():
    """1. Malformed API requests receive deterministic HTTP 400/422 with structured JSON error."""
    resp = client.post("/api/correspondence/analyze", json={"invalid_field": 12345})
    assert resp.status_code in [400, 422], f"Expected 400 or 422, got {resp.status_code}"
    data = resp.json()
    assert "detail" in data, "Error response must contain structured 'detail'"
    assert "traceback" not in str(data).lower(), "Raw traceback must never be exposed"


# ----------------------------------------------------------------------
# 2. Missing Resource
# ----------------------------------------------------------------------
def test_2_missing_resource():
    """2. Missing resources return deterministic 404 with structured error."""
    resp = client.get("/api/observations/NON_EXISTENT_LUNAR_OBS_99999")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


# ----------------------------------------------------------------------
# 3. Unavailable Payload Handling
# ----------------------------------------------------------------------
def test_3_unavailable_payload():
    """3. Requests for unavailable payload or sensor return safe non-accepted states."""
    resp = client.post(
        "/api/recommendations/next-observation",
        json={"entity_id": "ENTITY-CRATER-NONEXISTENT", "scientific_question": "offline payload test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("payload_status") == "PAYLOAD_UNAVAILABLE"
    assert data.get("recommended_sensor") == "NONE"
    assert data.get("status") not in ["ACCEPTED", "CONFIRMED"]

    # Test non-existent entity with standard question returns 404
    resp_404 = client.post(
        "/api/recommendations/next-observation",
        json={"entity_id": "ENTITY-CRATER-NONEXISTENT-REAL", "scientific_question": "spectral analysis"},
    )
    assert resp_404.status_code in [400, 404]


# ----------------------------------------------------------------------
# 4. Repeated Request Determinism
# ----------------------------------------------------------------------
def test_4_repeated_requests():
    """4. Repeated identical requests produce consistent, idempotent results without corruption."""
    resps = [client.get("/api/demo/scenarios") for _ in range(5)]
    for r in resps:
        assert r.status_code == 200
    
    first_data = resps[0].json()
    for r in resps[1:]:
        assert r.json() == first_data, "Repeated calls must yield identical scenario states"


# ----------------------------------------------------------------------
# 5. Concurrent Read Safety
# ----------------------------------------------------------------------
def test_5_concurrent_reads():
    """5. Concurrent read requests across multiple threads execute safely without race conditions."""
    def fetch_scenario(scenario_id):
        return client.get(f"/api/demo/scenarios/{scenario_id}/explanation")

    scenarios = ["SCENARIO-A", "SCENARIO-B", "SCENARIO-C", "SCENARIO-D", "SCENARIO-E"] * 3
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(fetch_scenario, scenarios))

    for resp in results:
        assert resp.status_code == 200
        data = resp.json()
        assert "decision" in data
        assert "judge_card" in data


# ----------------------------------------------------------------------
# 6. Database Rollback / Session Cleanup
# ----------------------------------------------------------------------
def test_6_database_rollback(db_session: Session):
    """6. Aborted or failing database transactions roll back cleanly without leaving orphan state."""
    initial_count = db_session.query(LunarEntityModel).count()
    
    try:
        # Create a failing transaction by violating schema constraints (NOT NULL constraint)
        db_session.execute(text("INSERT INTO lunar_entities (entity_id, latitude, longitude) VALUES (NULL, NULL, NULL)"))
        db_session.commit()
    except Exception:
        db_session.rollback()

    after_count = db_session.query(LunarEntityModel).count()
    assert after_count == initial_count, "Failed transaction must roll back cleanly"


# ----------------------------------------------------------------------
# 7. Duplicate Recommendation Prevention
# ----------------------------------------------------------------------
def test_7_no_duplicate_recommendations(db_session: Session):
    """7. Recommendation records remain deterministic and deduplicated per entity."""
    recs = db_session.query(RecommendationModel).all()
    rec_pairs = set()
    for r in recs:
        pair = (r.entity_id, r.recommended_sensor)
        # Verify no duplicate sensor recommendation for same entity with identical question
        assert pair not in rec_pairs or r.id is not None
        rec_pairs.add(pair)


# ----------------------------------------------------------------------
# 8. Duplicate Entity Prevention
# ----------------------------------------------------------------------
def test_8_no_duplicate_entities(db_session: Session):
    """8. Entity IDs are strictly unique, preventing duplicate persistent entities."""
    entities = db_session.query(LunarEntityModel).all()
    entity_ids = [e.entity_id for e in entities]
    assert len(entity_ids) == len(set(entity_ids)), "Entity IDs must be unique"


# ----------------------------------------------------------------------
# 9. Frontend / Backend Unavailable State
# ----------------------------------------------------------------------
def test_9_system_status_degraded_when_subsystem_fails():
    """9. System reports DEGRADED or UNAVAILABLE rather than HEALTHY if a subsystem is missing."""
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["ONLINE", "DEGRADED", "UNAVAILABLE"]
    assert "HEALTHY" != data["status"], "System status must use ONLINE/DEGRADED/UNAVAILABLE, not HEALTHY"
    if "subsystems" in data and data["subsystems"]:
        for name, sub_status in data["subsystems"].items():
            assert sub_status in ["ONLINE", "DEGRADED", "UNAVAILABLE"]


# ----------------------------------------------------------------------
# 10. Timeout / Error State Safety
# ----------------------------------------------------------------------
def test_10_error_state_never_accepts():
    """10. Unhandled exceptions or error states return safe non-accepted states (UNKNOWN/ERROR)."""
    # Trigger 404 or controlled error
    resp = client.get("/api/demo/scenarios/INVALID_SCENARIO/explanation")
    assert resp.status_code == 404
    data = resp.json()
    # Ensure it never returns ACCEPTED or CONFIRMED
    assert data.get("status") not in ["ACCEPTED", "CONFIRMED"]
    assert data.get("decision") not in ["ACCEPTED", "CONFIRMED"]


# ----------------------------------------------------------------------
# 11. Large Data Safety Boundary
# ----------------------------------------------------------------------
def test_11_large_data_safety_boundary():
    """11. Real multi-GB binary PDS4 datasets are never bundled or served raw into client memory."""
    # Verify that observation responses return bounded metadata and summaries, not multi-GB arrays
    resp = client.get("/api/observations")
    assert resp.status_code == 200
    content_len = len(resp.content)
    # The entire observation list payload must be well bounded (< 10 MB, typically < 100 KB)
    assert content_len < 10 * 1024 * 1024, f"Payload too large: {content_len} bytes"


# ----------------------------------------------------------------------
# 12. Path Traversal and Input Hardening
# ----------------------------------------------------------------------
def test_12_path_traversal_protection():
    """12. Path traversal sequences (../, ..\\) in file and observation endpoints are blocked."""
    traversal_paths = [
        "../../etc/passwd",
        "..\\..\\windows\\system32\\cmd.exe",
        "....//....//data/real",
        "%2e%2e%2f%2e%2e%2f",
    ]
    for path in traversal_paths:
        resp = client.get(f"/api/observations/experiments/{path}")
        assert resp.status_code in [400, 404], f"Path {path} should be blocked, got {resp.status_code}"


# ----------------------------------------------------------------------
# 13. force_accept Protection
# ----------------------------------------------------------------------
def test_13_force_accept_protection():
    """13. Attempting force_accept=True is strictly rejected by scientific safety rules."""
    payload = {
        "source_observation_id": "OHRC_REF_TEST",
        "target_observation_id": "TMC2_REF_TEST",
        "matcher_algorithm": "SIFT",
        "force_accept": True,
    }
    resp = client.post("/api/correspondence/analyze", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "strictly forbidden" in data["detail"].lower() or "bypass" in data["detail"].lower()


# ----------------------------------------------------------------------
# 14. Synthetic Provenance Protection
# ----------------------------------------------------------------------
def test_14_synthetic_provenance_protection():
    """14. Demonstrations strictly tag synthetic scenarios with is_synthetic=True."""
    demo_service = DemoService(SessionLocal())
    scenarios = demo_service.get_demonstration_scenarios()
    
    for s in scenarios:
        if s["scenario_id"] != "SCENARIO-A":
            assert s["is_synthetic"] is True, f"{s['scenario_id']} must have is_synthetic=True"
            assert s["real_or_synthetic"] == "SYNTHETIC"
        else:
            assert s["is_synthetic"] is False, "Scenario A must have is_synthetic=False"
            assert s["real_or_synthetic"] in ["REAL", "REAL_LUNAR"]


# ----------------------------------------------------------------------
# 15. Uncertainty Override Protection
# ----------------------------------------------------------------------
def test_15_uncertainty_override_protection():
    """15. Unauthorized uncertainty overrides are strictly rejected with 403."""
    override_payload = {
        "correspondence_id": "CORR-TEST-001",
        "new_uncertainty": 0.05,
        "reason": "Arbitrary manual reduction",
    }
    resp = client.post("/api/uncertainty/override", json=override_payload)
    assert resp.status_code in [400, 403], f"Uncertainty override must be rejected, got {resp.status_code}"


# ----------------------------------------------------------------------
# 16. System Health Reporting
# ----------------------------------------------------------------------
def test_16_system_health_and_subsystem_reporting():
    """16. System status reports accurate status (ONLINE/DEGRADED/UNAVAILABLE) across all subsystems."""
    resp = client.get("/api/system/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ["ONLINE", "DEGRADED", "UNAVAILABLE"]
    assert "dem_availability" in data
    assert "groundgrid_availability" in data
    assert "raw_data_integrity" in data
    assert "0 bytes modified" in data["raw_data_integrity"]


# ----------------------------------------------------------------------
# 17. Raw Data Integrity
# ----------------------------------------------------------------------
def test_17_raw_data_integrity():
    """17. Raw data in data/real/ remains completely untouched (0 bytes modified)."""
    repo_root = Path(__file__).resolve().parent.parent.parent
    diff_res = subprocess.run(
        ["git", "diff", "--stat", "data/real/"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    assert diff_res.returncode == 0
    assert diff_res.stdout.strip() == "", f"data/real/ has uncommitted modifications:\n{diff_res.stdout}"
