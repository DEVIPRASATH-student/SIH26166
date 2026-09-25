"""Lunar Entity and World Model Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class WorldModelHypothesisResponse(BaseModel):
    property_name: str
    hypothesis_value: str
    confidence: float
    uncertainty: float
    evidence_count: int
    supporting_evidence: List[str]
    conflicting_evidence: List[str]


class LunarEntityResponse(BaseModel):
    entity_id: str
    entity_type: str
    latitude: float
    longitude: float
    spatial_extent_m: float
    confidence: float
    uncertainty: float
    associated_observations_count: int
    sensors_present: List[str]
    is_synthetic: bool = True
    created_at: datetime


class EntityDetailResponse(BaseModel):
    entity_id: str
    entity_type: str
    latitude: float
    longitude: float
    spatial_extent_m: float
    confidence: float
    uncertainty: float
    morphology: Dict[str, Any]
    elevation: Dict[str, Any]
    spectral: Dict[str, Any]
    observations: List[Dict[str, Any]]
    hypotheses: List[WorldModelHypothesisResponse]
    is_synthetic: bool = True
    created_at: datetime
    updated_at: datetime
