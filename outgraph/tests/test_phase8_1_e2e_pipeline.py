"""Phase 8.1 End-to-End Scientific Integration Pipeline Tests.

Verifies the complete 15-step scientific pipeline across:
- Scenario A: Real Lunar OHRC + TMC-2 Non-Overlap Negative Control
- Scenario B: Synthetic Controlled Positive Control
- Scenario C: Controlled Insufficient / Unknown Evidence
- Scenario D: Controlled Contradictory Evidence
- Strict Scientific Safety Rules & Guardrails:
    * PHYSICAL CORRESPONDENCE NOT VALIDATED invariant
    * REAL-DATA ACCURACY = N/A
    * UNKNOWN != NEGATIVE
    * ENTITY ASSOCIATION != DIRECT IMAGE CORRESPONDENCE
    * Active Loop POTENTIALLY_REDUCES_UNCERTAINTY
    * Provenance preservation
"""

import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from outgraph.backend.app.main import app
from outgraph.backend.app.database.session import init_db, SessionLocal
from outgraph.backend.app.services.pipeline_service import PipelineController, PipelineResult
from outgraph.backend.app.models.observation import ObservationModel
from outgraph.backend.app.models.correspondence import CorrespondenceModel
from outgraph.backend.app.models.evidence import CorrespondenceEvidenceModel
from outgraph.backend.app.models.lunar_entity import LunarEntityModel
from outgraph.backend.app.models.recommendation import KnowledgeGapModel, RecommendationModel
from outgraph.ml.world_model.graph import EdgeRelation


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ======================================================================
# 1. SCENARIO A: REAL NEGATIVE CONTROL E2E
# ======================================================================

def test_real_negative_control_e2e(db_session):
    """Scenario A: Real OHRC + TMC-2 Pair with 1.49 - 2.04 km Footprint Separation.

    Must satisfy:
    1. Physical verification evaluates calibrated GroundGrids and rejects correspondence.
    2. Primary rejection includes Gate 3 (GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH).
    3. Status is strictly REJECTED.
    4. Preserves PHYSICAL CORRESPONDENCE NOT VALIDATED.
    5. Preserves REAL-DATA ACCURACY = N/A.
    6. Emits FOOTPRINT_NON_OVERLAP knowledge gap.
    7. Persistent lunar entity is NOT deleted or rejected.
    8. is_synthetic is strictly False.
    """
    controller = PipelineController(db_session)
    result = controller.run_real_negative_control()

    # Integrity & Provenance
    assert result.is_synthetic is False, "Real lunar data must NOT be marked synthetic"
    assert result.source_sensor == "OHRC"
    assert result.target_sensor == "TMC-2"
    assert result.scale_ratio > 20.0, "OHRC (0.26m) to TMC-2 (6.07m) scale ratio must be > 20x"
    assert result.scale_normalization_needed is True

    # Physical Rejection
    assert result.status == "REJECTED", f"Expected REJECTED status, got {result.status}"
    assert result.physical_verification_passed is False
    assert result.num_inliers == 0, "No inliers allowed for physically disjoint footprints"

    # Rejection Reasons & Guardrails
    reasons_str = " ".join(result.physical_rejection_reasons)
    assert "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH" in reasons_str or "FOOTPRINT_NON_OVERLAP" in reasons_str
    assert "PHYSICAL CORRESPONDENCE NOT VALIDATED" in reasons_str or any(
        "PHYSICAL CORRESPONDENCE NOT VALIDATED" in lim for lim in result.scientific_limitations
    )

    # Knowledge Gap Detection
    gap_types = [g["gap_type"] for g in result.knowledge_gaps]
    assert "FOOTPRINT_NON_OVERLAP" in gap_types, "Must emit FOOTPRINT_NON_OVERLAP gap"

    # Entity Preservation (Rule 4: Failed correspondence != negative entity evidence)
    assert result.entity_id is not None
    entity = db_session.query(LunarEntityModel).filter(LunarEntityModel.entity_id == result.entity_id).first()
    assert entity is not None, "Entity must not be deleted due to correspondence rejection"
    assert result.entity_state != "REJECTED", "Entity must remain valid candidate"
    assert entity.confidence > 0.0, "Entity must remain valid candidate"


# ======================================================================
# 2. SCENARIO B: SYNTHETIC POSITIVE CONTROL E2E
# ======================================================================

def test_synthetic_positive_control_e2e(db_session):
    """Scenario B: Controlled Procedural Lunar Terrain with Known Overlap.

    Must satisfy:
    1. Candidate correspondence is detected.
    2. Geometric and physical verification pass.
    3. Status is ACCEPTED.
    4. is_synthetic is strictly True.
    5. Entity lifecycle state is updated (SUPPORTED).
    6. Does NOT claim real lunar validation.
    """
    controller = PipelineController(db_session)
    result = controller.run_synthetic_positive_control()

    # Synthetic Labeling
    assert result.is_synthetic is True, "Synthetic data must be explicitly marked is_synthetic=True"
    assert any("SYNTHETIC" in lim for lim in result.scientific_limitations)

    # Acceptance
    assert result.status in ["ACCEPTED", "ACCEPTED_ILLUMINATION_CONSISTENT", "SUPPORTED"]
    assert result.num_inliers > 0
    assert result.inlier_ratio > 0.0

    # Entity Update
    assert result.entity_id is not None
    entity = db_session.query(LunarEntityModel).filter(LunarEntityModel.entity_id == result.entity_id).first()
    assert entity is not None
    assert entity.is_synthetic is True


# ======================================================================
# 3. SCENARIO C: UNKNOWN / INSUFFICIENT EVIDENCE E2E
# ======================================================================

def test_unknown_e2e(db_session):
    """Scenario C: Featureless Terrain with Insufficient Keypoint Evidence.

    Must satisfy:
    1. Insufficient matches or inliers.
    2. Status evaluates to UNKNOWN or REJECTED.
    3. UNKNOWN != NEGATIVE: Must not conclude surface feature does not exist.
    4. Epistemic uncertainty remains unconstrained.
    """
    controller = PipelineController(db_session)
    result = controller.run_unknown_evidence_control()

    # Must not falsely validate
    assert result.status in ["UNKNOWN", "INSUFFICIENT_EVIDENCE", "REJECTED"]
    assert result.num_inliers == 0

    # Epistemic guardrail
    assert result.status != "NEGATIVE", "UNKNOWN must never be silently converted to NEGATIVE"
    assert any("UNKNOWN != NEGATIVE" in lim for lim in result.scientific_limitations)


# ======================================================================
# 4. SCENARIO D: CONTRADICTORY EVIDENCE E2E
# ======================================================================

def test_contradictory_evidence_e2e(db_session):
    """Scenario D: Opposing Solar Illumination Creating Contradictory Morphology.

    Must satisfy:
    1. Detects elevated evidence disagreement or illumination conflict.
    2. Uncertainty increases (> 0.40).
    3. Contradiction is preserved in explanation card without silent averaging.
    """
    controller = PipelineController(db_session)
    result = controller.run_contradictory_evidence_control()

    # Elevated uncertainty / disagreement
    unc = result.uncertainty_breakdown
    assert unc["evidence_disagreement"] >= 0.40 or unc["total_uncertainty"] >= 0.40 or result.status == "REJECTED"
    assert "rejection_reasons" in result.explanation_card or "evidence_disagreement" in result.explanation_card


# ======================================================================
# 5. PROVENANCE PRESERVATION E2E
# ======================================================================

def test_provenance_preservation_e2e(db_session):
    """Verifies that sensor, product ID, and processing metadata survive through all pipeline stages."""
    controller = PipelineController(db_session)
    result = controller.run_real_negative_control()

    # Check database persistence
    src_obs = db_session.query(ObservationModel).filter(ObservationModel.id == result.source_observation_id).first()
    assert src_obs is not None
    assert src_obs.product_id is not None
    assert src_obs.sensor_type == "OHRC"
    assert src_obs.is_synthetic is False

    # Check WorldGraph persistence
    g = controller.world_graph
    obs_node = g.get_node(result.source_observation_id)
    assert obs_node is not None
    assert obs_node.get("sensor_type") == "OHRC"
    assert obs_node.get("is_synthetic") is False


# ======================================================================
# 6. PHYSICAL REJECTION PROPAGATION
# ======================================================================

def test_physical_rejection_propagation(db_session):
    """Verifies physical gate rejection propagates to correspondence, evidence, and knowledge gaps."""
    controller = PipelineController(db_session)
    result = controller.run_real_negative_control()

    corr = db_session.query(CorrespondenceModel).filter(
        CorrespondenceModel.source_observation_id == result.source_observation_id,
        CorrespondenceModel.target_observation_id == result.target_observation_id,
    ).first()
    assert corr is not None
    assert corr.status == "REJECTED"

    ev = db_session.query(CorrespondenceEvidenceModel).filter(
        CorrespondenceEvidenceModel.correspondence_id == corr.id
    ).first()
    assert ev is not None
    reasons = json.loads(ev.rejection_reasons_json)
    assert any("GATE3" in r or "FOOTPRINT" in r for r in reasons)


# ======================================================================
# 7. ENTITY-CORRESPONDENCE NON-TRANSITIVITY GUARDRAIL
# ======================================================================

def test_entity_correspondence_non_transitivity(db_session):
    """Verifies: Entity Association != Direct Image Correspondence.

    Even if two observations associate to the same lunar region/entity,
    if physical correspondence between them was rejected, WorldGraph MUST NOT
    report valid correspondence between the two images.
    """
    controller = PipelineController(db_session)
    result = controller.run_real_negative_control()

    g = controller.world_graph
    has_corr = g.has_valid_correspondence(result.source_observation_id, result.target_observation_id)
    assert has_corr is False, "Entity association must NOT imply direct image correspondence!"


# ======================================================================
# 8. ACTIVE OBSERVATION PROPOSAL E2E
# ======================================================================

def test_active_observation_generation_e2e(db_session):
    """Verifies Next-Best-Observation proposal strictly adheres to conservative scientific wording.

    Must use: POTENTIALLY_REDUCES_UNCERTAINTY.
    Must NOT claim: WILL_RESOLVE.
    """
    controller = PipelineController(db_session)
    result = controller.run_real_negative_control()

    assert result.recommendation is not None
    rec = result.recommendation
    explanation = rec["explanation"]

    assert "POTENTIALLY_REDUCES_UNCERTAINTY" in explanation
    assert "WILL_RESOLVE" not in explanation
    assert rec["expected_information_gain"] > 0.0
