"""Test Suite for Uncertainty Engine & Persistent Entities."""

import pytest
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from outgraph.backend.app.database.session import Base
from outgraph.backend.app.services.entity_service import EntityService
from outgraph.backend.app.services.graph_service import GraphService
from outgraph.backend.app.services.knowledge_gap_service import KnowledgeGapService
from outgraph.backend.app.services.recommendation_service import RecommendationService
from outgraph.ml.uncertainty.uncertainty_engine import UncertaintyEngine
from outgraph.ml.verification.physics_engine import PhysicsEvidenceProfile


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


from outgraph.ml.verification.geometry import GeometryVerificationResult

def test_uncertainty_quantification():
    engine = UncertaintyEngine()

    geo_res_good = GeometryVerificationResult(
        is_valid=True,
        geometry_score=0.95,
        inlier_mask=np.ones(10, dtype=bool),
        num_inliers=10,
        inlier_ratio=0.85,
        mean_reprojection_error_px=0.45,
        condition_number=1.2,
    )

    # Case A: High agreement profile
    profile_good = PhysicsEvidenceProfile(
        visual_score=0.92,
        geometry_score=0.95,
        illumination_score=0.90,
        terrain_score=0.88,
        scale_score=0.94,
        spatial_score=0.91,
        overall_confidence=0.92,
        status="VERIFIED",
        geometry_result=geo_res_good,
        metadata={"inlier_ratio": 0.85},
    )
    unc_good = engine.compute_correspondence_uncertainty(profile_good)
    assert unc_good.total_uncertainty < 0.35
    assert "LOW_UNCERTAINTY" in unc_good.calibration_status

    # Case B: High visual match but low physics score (epistemic conflict)
    profile_conflict = PhysicsEvidenceProfile(
        visual_score=0.95,
        geometry_score=0.20,
        illumination_score=0.15,
        terrain_score=0.10,
        scale_score=0.80,
        spatial_score=0.25,
        overall_confidence=0.35,
        status="REJECTED",
        metadata={"inlier_ratio": 0.15},
    )
    unc_conflict = engine.compute_correspondence_uncertainty(profile_conflict)
    assert unc_conflict.evidence_disagreement > 0.40
    assert unc_conflict.total_uncertainty > 0.50
    assert unc_conflict.calibration_status == "HIGH_EPISTEMIC_RISK"


def test_entity_resolution_and_hypotheses(in_memory_db):
    entity_service = EntityService(in_memory_db)

    # 1. Resolve new entity
    e1 = entity_service.resolve_entity(
        lat=-70.50,
        lon=22.80,
        entity_type="crater",
        spatial_extent_m=200.0,
        sensor_type="OHRC",
    )
    assert "LUNAR-ENTITY-" in e1.entity_id

    # 2. Resolve nearby observation (should attach to same persistent entity)
    e2 = entity_service.resolve_entity(
        lat=-70.501,  # within 0.005 deg tolerance
        lon=22.801,
        entity_type="crater",
        sensor_type="TMC-2",
    )
    assert e1.entity_id == e2.entity_id

    # 3. Check Hypotheses
    hypotheses = entity_service.get_entity_hypotheses(e1.entity_id)
    assert len(hypotheses) >= 3


def test_knowledge_gaps_and_recommendation(in_memory_db):
    entity_service = EntityService(in_memory_db)
    gap_service = KnowledgeGapService(in_memory_db)
    rec_service = RecommendationService(in_memory_db)

    # Create entity with OHRC only
    e = entity_service.resolve_entity(lat=-75.0, lon=30.0, entity_type="crater", sensor_type="OHRC")

    # Scan gaps (should detect missing IIRS spectral data)
    gaps = gap_service.scan_knowledge_gaps()
    assert any(g.gap_type == "MISSING_SPECTRAL_EVIDENCE" for g in gaps)

    # Next-Best Observation recommendation
    rec = rec_service.recommend_next_observation(e.entity_id, "spectral analysis")
    assert rec.recommended_sensor == "IIRS"
    assert rec.expected_information_gain > 0.0
