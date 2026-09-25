"""Persistent Lunar Entity and Observation Association Engine.
Stage 4.1: Physics-Aware Observation -> Entity Association.

Provides strict state machines, association tracking, provenance preservation,
and rejection of ungrounded or geographically disjoint associations.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import uuid
import math
from pydantic import BaseModel, Field


class EntityState(str, Enum):
    """Scientific confirmation state of a persistent lunar entity."""
    CANDIDATE = "CANDIDATE"
    SUPPORTED = "SUPPORTED"
    CONFIRMED = "CONFIRMED"
    CONTRADICTED = "CONTRADICTED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class AssociationType(str, Enum):
    """Nature of the relationship between an observation and an entity."""
    DIRECT = "DIRECT"
    GEOMETRIC = "GEOMETRIC"
    MULTIMODAL = "MULTIMODAL"
    TEMPORAL = "TEMPORAL"
    HYPOTHESIZED = "HYPOTHESIZED"
    UNVALIDATED = "UNVALIDATED"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"


class AssociationStatus(str, Enum):
    """Scientific status of the observation-to-entity association."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVALIDATED = "UNVALIDATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AssociationProvenance(BaseModel):
    """Immutable provenance record for an observation association."""
    source_observation_id: str
    source_sensor: str
    source_product_id: Optional[str] = None
    source_processing_stage: str = "PHASE4_STAGE1_ENTITY_ASSOCIATION"
    source_method: str = "GEODETIC_RADIUS_RESOLUTION"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class EntityAssociation(BaseModel):
    """Explicit association between a lunar observation and a persistent entity."""
    association_id: str = Field(default_factory=lambda: f"ASSOC-{uuid.uuid4().hex[:8].upper()}")
    entity_id: str
    observation_id: str
    association_type: AssociationType = AssociationType.UNVALIDATED
    status: AssociationStatus = AssociationStatus.UNVALIDATED
    method: str = "SPATIAL_PROXIMITY"
    confidence: Optional[float] = None
    uncertainty: Optional[float] = None
    geometric_distance_m: Optional[float] = None
    provenance: AssociationProvenance
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rejection_reason: Optional[str] = None

    model_config = {"frozen": False}


class LunarEntity(BaseModel):
    """Persistent physical or scientifically meaningful lunar surface entity."""
    entity_id: str
    entity_type: str = "crater"  # crater, boulder_field, ridge, rille, terrain_region, albedo_feature, spectral_anomaly, unknown_candidate
    state: EntityState = EntityState.CANDIDATE
    latitude: float
    longitude: float
    elevation_m: Optional[float] = None
    spatial_extent_m: float = 100.0

    # Explicit uncertainty interval or scalar
    uncertainty_m: Optional[float] = None
    confidence: Optional[float] = None

    associations: List[EntityAssociation] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_association(self, observation_id: str) -> Optional[EntityAssociation]:
        """Finds existing association by observation ID."""
        for assoc in self.associations:
            if assoc.observation_id == observation_id:
                return assoc
        return None

    def add_or_update_association(self, new_assoc: EntityAssociation) -> None:
        """Adds or updates an association, preventing duplicate conflicting records."""
        existing = self.get_association(new_assoc.observation_id)
        if existing:
            # Update existing association
            idx = self.associations.index(existing)
            self.associations[idx] = new_assoc
        else:
            self.associations.append(new_assoc)
        self.updated_at = datetime.utcnow()
        self._refresh_entity_state()

    def _refresh_entity_state(self) -> None:
        """Updates entity state based on the aggregation of association statuses."""
        supported = [a for a in self.associations if a.status == AssociationStatus.SUPPORTED]
        rejected = [a for a in self.associations if a.status == AssociationStatus.REJECTED]
        contradicted = [a for a in self.associations if a.status == AssociationStatus.CONTRADICTED]

        if contradicted:
            self.state = EntityState.CONTRADICTED
        elif len(supported) >= 2:
            self.state = EntityState.CONFIRMED
        elif len(supported) == 1:
            self.state = EntityState.SUPPORTED
        elif rejected and not supported:
            self.state = EntityState.REJECTED
        else:
            self.state = EntityState.CANDIDATE


class EntityResolver:
    """Manages persistent entity resolution, association matching, and rejection enforcement."""

    MOON_RADIUS_M = 1737400.0

    def __init__(self, spatial_tolerance_m: float = 200.0):
        self.spatial_tolerance_m = spatial_tolerance_m
        self.entities: Dict[str, LunarEntity] = {}

    def haversine_distance_m(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates great-circle distance on the spherical lunar surface."""
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlam = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return self.MOON_RADIUS_M * c

    def create_entity(
        self,
        latitude: float,
        longitude: float,
        entity_type: str = "crater",
        spatial_extent_m: float = 100.0,
        elevation_m: Optional[float] = None,
        entity_id: Optional[str] = None,
        initial_state: EntityState = EntityState.CANDIDATE,
        properties: Optional[Dict[str, Any]] = None,
    ) -> LunarEntity:
        """Explicitly creates a persistent lunar entity."""
        if entity_id is None:
            entity_id = f"LUNAR-ENT-{uuid.uuid4().hex[:6].upper()}"

        entity = LunarEntity(
            entity_id=entity_id,
            entity_type=entity_type,
            state=initial_state,
            latitude=latitude,
            longitude=longitude,
            elevation_m=elevation_m,
            spatial_extent_m=spatial_extent_m,
            properties=properties or {},
        )
        self.entities[entity_id] = entity
        return entity

    def associate_observation(
        self,
        entity_id: str,
        observation_id: str,
        obs_lat: float,
        obs_lon: float,
        sensor_type: str,
        product_id: Optional[str] = None,
        method: str = "GEODETIC_RADIUS_RESOLUTION",
        confidence: Optional[float] = None,
        uncertainty: Optional[float] = None,
        notes: Optional[str] = None,
        force_rejection: bool = False,
        rejection_reason: Optional[str] = None,
    ) -> EntityAssociation:
        """Associates an observation with an entity, enforcing spatial gating and rejection rules."""
        if entity_id not in self.entities:
            raise KeyError(f"Entity '{entity_id}' does not exist in registry.")

        entity = self.entities[entity_id]
        distance_m = self.haversine_distance_m(entity.latitude, entity.longitude, obs_lat, obs_lon)

        prov = AssociationProvenance(
            source_observation_id=observation_id,
            source_sensor=sensor_type,
            source_product_id=product_id,
            source_method=method,
            notes=notes,
        )

        if force_rejection:
            assoc = EntityAssociation(
                entity_id=entity_id,
                observation_id=observation_id,
                association_type=AssociationType.REJECTED,
                status=AssociationStatus.REJECTED,
                method=method,
                geometric_distance_m=distance_m,
                confidence=0.0,
                uncertainty=1.0,
                provenance=prov,
                rejection_reason=rejection_reason or "MANUALLY_REJECTED",
            )
        elif distance_m > self.spatial_tolerance_m:
            # Point is beyond spatial tolerance: do NOT fabricate association!
            assoc = EntityAssociation(
                entity_id=entity_id,
                observation_id=observation_id,
                association_type=AssociationType.REJECTED,
                status=AssociationStatus.REJECTED,
                method=method,
                geometric_distance_m=distance_m,
                confidence=0.0,
                uncertainty=1.0,
                provenance=prov,
                rejection_reason=f"SPATIAL_DISTANCE_EXCEEDS_TOLERANCE: {distance_m:.1f}m > {self.spatial_tolerance_m:.1f}m",
            )
        else:
            # Spatial distance is within tolerance
            assoc = EntityAssociation(
                entity_id=entity_id,
                observation_id=observation_id,
                association_type=AssociationType.GEOMETRIC,
                status=AssociationStatus.SUPPORTED,
                method=method,
                geometric_distance_m=distance_m,
                confidence=confidence,
                uncertainty=uncertainty,
                provenance=prov,
            )

        entity.add_or_update_association(assoc)
        return assoc
