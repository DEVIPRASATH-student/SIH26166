"""Lunar Entity API Endpoints."""

import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.entity_service import EntityService
from ...schemas.entity import LunarEntityResponse, EntityDetailResponse, WorldModelHypothesisResponse
from ...models.lunar_entity import LunarEntityModel

router = APIRouter(prefix="/entities", tags=["Lunar Entities"])


@router.get("", response_model=List[LunarEntityResponse])
def list_entities(db: Session = Depends(get_db)):
    """Lists all persistent lunar physical entities."""
    entity_service = EntityService(db)
    entities = entity_service.list_entities()
    result = []

    for e in entities:
        obs_list = entity_service.get_entity_observations(e.entity_id)
        sensors = list({o.sensor_type for o in obs_list})
        result.append(
            LunarEntityResponse(
                entity_id=e.entity_id,
                entity_type=e.entity_type,
                latitude=e.latitude,
                longitude=e.longitude,
                spatial_extent_m=e.spatial_extent_m,
                confidence=e.confidence,
                uncertainty=e.uncertainty,
                associated_observations_count=len(obs_list),
                sensors_present=sensors,
                is_synthetic=e.is_synthetic,
                created_at=e.created_at,
            )
        )
    return result


@router.get("/{entity_id}", response_model=EntityDetailResponse)
def get_entity_detail(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves full physical profile, observation history, and world model hypotheses for an entity."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

    obs_list = entity_service.get_entity_observations(entity.entity_id)
    hyp_list = entity_service.get_entity_hypotheses(entity.entity_id)

    obs_dicts = []
    for o in obs_list:
        obs_dicts.append({
            "observation_id": o.observation_id,
            "sensor_type": o.sensor_type,
            "correspondence_id": o.correspondence_id,
            "attached_at": o.attached_at.isoformat(),
            "confidence": o.confidence,
        })

    hyp_res = []
    for h in hyp_list:
        hyp_res.append(
            WorldModelHypothesisResponse(
                property_name=h.property_name,
                hypothesis_value=h.hypothesis_value,
                confidence=h.confidence,
                uncertainty=h.uncertainty,
                evidence_count=h.evidence_count,
                supporting_evidence=json.loads(h.supporting_evidence_json) if h.supporting_evidence_json else [],
                conflicting_evidence=json.loads(h.conflicting_evidence_json) if h.conflicting_evidence_json else [],
            )
        )

    return EntityDetailResponse(
        entity_id=entity.entity_id,
        entity_type=entity.entity_type,
        latitude=entity.latitude,
        longitude=entity.longitude,
        spatial_extent_m=entity.spatial_extent_m,
        confidence=entity.confidence,
        uncertainty=entity.uncertainty,
        morphology=json.loads(entity.morphology_json) if entity.morphology_json else {},
        elevation=json.loads(entity.elevation_json) if entity.elevation_json else {},
        spectral=json.loads(entity.spectral_json) if entity.spectral_json else {},
        observations=obs_dicts,
        hypotheses=hyp_res,
        is_synthetic=entity.is_synthetic,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get("/{entity_id}/evidence")
def get_entity_evidence(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves fused multi-sensor evidence breakdown and timeline."""
    return get_entity_detail(entity_id, db)


@router.get("/{entity_id}/observations")
def get_entity_observations_endpoint(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves list of sensor observations associated with this entity."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    obs_list = entity_service.get_entity_observations(entity_id)
    return [
        {
            "observation_id": o.observation_id,
            "sensor_type": o.sensor_type,
            "correspondence_id": o.correspondence_id,
            "attached_at": o.attached_at.isoformat(),
            "confidence": o.confidence,
        }
        for o in obs_list
    ]


@router.get("/{entity_id}/uncertainty")
def get_entity_uncertainty_endpoint(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves quantitative and qualitative uncertainty decomposition for an entity."""
    entity_service = EntityService(db)
    entity = entity_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    return {
        "entity_id": entity.entity_id,
        "confidence": entity.confidence,
        "uncertainty": entity.uncertainty,
        "spatial_extent_m": entity.spatial_extent_m,
        "source": "FUSED_WORLD_MODEL_UNCERTAINTY",
    }


@router.get("/{entity_id}/gaps")
def get_entity_gaps_endpoint(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves prioritized knowledge gaps specific to this entity."""
    from ...services.knowledge_gap_service import KnowledgeGapService
    gap_service = KnowledgeGapService(db)
    all_gaps = gap_service.list_gaps()
    entity_gaps = [g for g in all_gaps if g.entity_id == entity_id]
    return [
        {
            "id": g.id,
            "entity_id": g.entity_id,
            "gap_type": g.gap_type,
            "severity": g.severity,
            "reason": g.reason,
            "recommended_sensor": g.recommended_sensor,
            "status": g.status,
            "created_at": g.created_at.isoformat(),
        }
        for g in entity_gaps
    ]


@router.get("/{entity_id}/recommendations")
def get_entity_recommendations_endpoint(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves next-best observation recommendations for this entity."""
    from ...services.recommendation_service import RecommendationService
    rec_service = RecommendationService(db)
    try:
        rec = rec_service.recommend_next_observation(entity_id=entity_id)
        return {
            "entity_id": entity_id,
            "recommended_sensor": rec.recommended_sensor,
            "expected_information_gain": rec.expected_information_gain,
            "uncertainty_reduction": rec.uncertainty_reduction,
            "explanation": rec.explanation,
        }
    except Exception as e:
        return {"entity_id": entity_id, "recommendations": []}

