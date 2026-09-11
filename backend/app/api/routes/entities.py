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
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get("/{entity_id}/evidence")
def get_entity_evidence(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves fused multi-sensor evidence breakdown and timeline."""
    return get_entity_detail(entity_id, db)
