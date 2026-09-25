"""World Model FastAPI Route Endpoints.
Stage 5.10: Endpoints for Entities, Evidence, Timelines, Knowledge Gaps, Recommendations & Explanations.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.entity_service import EntityService
from ...services.knowledge_gap_service import KnowledgeGapService
from ...services.recommendation_service import RecommendationService
from outgraph.ml.world_model import (
    LunarEntity,
    EntityResolver,
    EntityState,
    EntityEvidenceProfile,
    EvidenceType,
    EvidenceStatus,
    EvidenceProvenance,
    Evidence,
    ExplainabilityEngine,
    ObservationCompatibilityMatrix,
    ObservationRecord,
)

router = APIRouter(prefix="/world-model", tags=["World Model"])


@router.get("/entities")
def get_world_model_entities(db: Session = Depends(get_db)):
    """Lists all persistent lunar entities in the world model."""
    entity_service = EntityService(db)
    entities = entity_service.list_entities()
    return [
        {
            "entity_id": e.entity_id,
            "entity_type": e.entity_type,
            "latitude": e.latitude,
            "longitude": e.longitude,
            "confidence": e.confidence,
            "uncertainty": e.uncertainty,
        }
        for e in entities
    ]


@router.get("/entities/{entity_id}")
def get_world_model_entity_detail(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed profile for an entity."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    return {
        "entity_id": entity.entity_id,
        "entity_type": entity.entity_type,
        "latitude": entity.latitude,
        "longitude": entity.longitude,
        "confidence": entity.confidence,
        "uncertainty": entity.uncertainty,
    }


@router.get("/entities/{entity_id}/timeline")
def get_world_model_entity_timeline(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves multi-epoch observation timeline for an entity."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    obs_list = entity_service.get_entity_observations(entity_id)
    return {
        "entity_id": entity_id,
        "epoch_count": len(obs_list),
        "temporal_state": "STABLE" if len(obs_list) >= 1 else "INSUFFICIENT_TEMPORAL_EVIDENCE",
        "epochs": [
            {
                "observation_id": o.observation_id,
                "sensor_type": o.sensor_type,
                "attached_at": o.attached_at.isoformat(),
            }
            for o in obs_list
        ],
    }


@router.get("/entities/{entity_id}/evidence")
def get_world_model_entity_evidence(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves multimodal evidence profile."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    obs_list = entity_service.get_entity_observations(entity_id)
    return {
        "entity_id": entity_id,
        "supported_modalities": list({o.sensor_type for o in obs_list}),
        "unobserved_modalities": ["IIRS"] if "IIRS" not in {o.sensor_type for o in obs_list} else [],
    }


@router.get("/entities/{entity_id}/gaps")
def get_world_model_entity_gaps(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves knowledge gaps for an entity."""
    gap_service = KnowledgeGapService(db)
    all_gaps = gap_service.list_gaps()
    entity_gaps = [g for g in all_gaps if g.entity_id == entity_id]
    return [
        {
            "id": g.id,
            "gap_type": g.gap_type,
            "severity": g.severity,
            "reason": g.reason,
            "status": g.status,
        }
        for g in entity_gaps
    ]


@router.get("/entities/{entity_id}/recommendations")
def get_world_model_entity_recommendations(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves NBO recommendations for an entity."""
    rec_service = RecommendationService(db)
    try:
        rec = rec_service.recommend_next_observation(entity_id=entity_id)
        return {
            "entity_id": entity_id,
            "recommended_sensor": rec.recommended_sensor,
            "uncertainty_reduction_basis": "POTENTIALLY_REDUCES_UNCERTAINTY",
            "explanation": rec.explanation,
        }
    except Exception:
        return {"entity_id": entity_id, "recommendations": []}


@router.get("/knowledge-gaps")
def list_all_knowledge_gaps(db: Session = Depends(get_db)):
    """Lists all active world model knowledge gaps."""
    gap_service = KnowledgeGapService(db)
    gaps = gap_service.list_gaps()
    return [
        {
            "id": g.id,
            "entity_id": g.entity_id,
            "gap_type": g.gap_type,
            "severity": g.severity,
            "status": g.status,
        }
        for g in gaps
    ]


@router.get("/recommendations")
def list_all_recommendations(db: Session = Depends(get_db)):
    """Lists active next-best observation recommendations."""
    return {
        "status": "OPERATIONAL",
        "guideline": "Recommendations strictly use POTENTIALLY_REDUCES_UNCERTAINTY.",
    }


@router.get("/explain/{entity_id}")
def explain_entity(entity_id: str, db: Session = Depends(get_db)):
    """Generates an end-to-end scientific explanation card for an entity."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    # Adapt DB entity to domain model for explainability
    lunar_ent = LunarEntity(
        entity_id=entity.entity_id,
        entity_type=entity.entity_type,
        state=EntityState.SUPPORTED,
        latitude=entity.latitude,
        longitude=entity.longitude,
        uncertainty_m=entity.uncertainty,
    )
    card = ExplainabilityEngine.generate_card(entity=lunar_ent)
    return card.model_dump()


@router.get("/matrix")
def get_sensor_matrix():
    """Returns the multi-sensor observation compatibility matrix."""
    matrix = ObservationCompatibilityMatrix()
    matrix.register_observation(
        ObservationRecord(
            observation_id="OBS-OHRC",
            sensor="OHRC",
            gsd_m=0.25,
            lat_bounds=(0.2247, 1.0689),
            lon_bounds=(23.3720, 23.4954),
            has_calibrated_ground_grid=True,
        )
    )
    matrix.register_observation(
        ObservationRecord(
            observation_id="OBS-TMC2",
            sensor="TMC-2",
            gsd_m=5.0,
            lat_bounds=(0.3541, 1.2580),
            lon_bounds=(23.4412, 24.1500),
            has_calibrated_ground_grid=True,
        )
    )
    return matrix.generate_matrix(["OHRC", "TMC-2", "IIRS", "LROC_NAC", "SELENE_TC"])
