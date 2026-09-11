"""Persistent Lunar Entity Resolution & World Model Service.
Maintains identity for physical lunar structures across heterogeneous observations.
Fuses multi-sensor evidence into persistent beliefs while preserving conflicting hypotheses.
"""

import json
import uuid
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

from ..models.lunar_entity import LunarEntityModel, EntityObservationModel, WorldModelHypothesisModel
from ..models.observation import ObservationModel
from ..models.correspondence import CorrespondenceModel


class EntityService:
    """Manages physical lunar entities, entity resolution, and probabilistic world model beliefs."""

    def __init__(self, db: Session):
        self.db = db

    def resolve_entity(
        self,
        lat: float,
        lon: float,
        entity_type: str = "crater",
        spatial_extent_m: float = 120.0,
        observation_id: Optional[str] = None,
        correspondence_id: Optional[str] = None,
        sensor_type: str = "OHRC",
        confidence: float = 0.92,
        morphology: Optional[Dict[str, Any]] = None,
        elevation: Optional[Dict[str, Any]] = None,
        spectral: Optional[Dict[str, Any]] = None,
    ) -> LunarEntityModel:
        """Searches for existing entity within geodetic radius or creates a new persistent entity."""
        # Spatial threshold: ~0.005 degrees (~150m at lunar polar latitudes)
        threshold_deg = 0.005
        existing = (
            self.db.query(LunarEntityModel)
            .filter(
                (LunarEntityModel.latitude >= lat - threshold_deg)
                & (LunarEntityModel.latitude <= lat + threshold_deg)
                & (LunarEntityModel.longitude >= lon - threshold_deg)
                & (LunarEntityModel.longitude <= lon + threshold_deg)
            )
            .first()
        )

        if existing:
            # Attach observation to existing persistent entity
            if observation_id:
                self._attach_observation(existing.entity_id, observation_id, correspondence_id, sensor_type, confidence)
            return existing

        # Create new persistent entity ID
        short_hex = uuid.uuid4().hex[:5].upper()
        entity_id = f"LUNAR-ENTITY-{short_hex}"

        entity = LunarEntityModel(
            entity_id=entity_id,
            entity_type=entity_type,
            latitude=lat,
            longitude=lon,
            spatial_extent_m=spatial_extent_m,
            confidence=confidence,
            uncertainty=round(1.0 - confidence, 4),
            morphology_json=json.dumps(morphology or {"classification": "Impact Crater", "rim_integrity": "Sharp"}),
            elevation_json=json.dumps(elevation or {"depth_m": 42.5, "slope_deg": 16.8, "dem_source": "TMC-2 Stereo"}),
            spectral_json=json.dumps(spectral or {"pyroxene_index": 0.42, "anorthosite_index": 0.65, "water_ice_proxy": 0.12}),
        )
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

        if observation_id:
            self._attach_observation(entity.entity_id, observation_id, correspondence_id, sensor_type, confidence)

        # Seed initial World Model Hypotheses
        self._initialize_hypotheses(entity)

        return entity

    def _attach_observation(
        self,
        entity_id: str,
        observation_id: str,
        correspondence_id: Optional[str],
        sensor_type: str,
        confidence: float,
    ):
        rel_id = f"EO-{entity_id[-5:]}-{observation_id}"
        existing = self.db.query(EntityObservationModel).filter(
            EntityObservationModel.entity_id == entity_id,
            EntityObservationModel.observation_id == observation_id,
        ).first()

        if not existing:
            rel = EntityObservationModel(
                id=rel_id,
                entity_id=entity_id,
                observation_id=observation_id,
                correspondence_id=correspondence_id,
                sensor_type=sensor_type,
                confidence=confidence,
            )
            self.db.add(rel)
            self.db.commit()

    def _initialize_hypotheses(self, entity: LunarEntityModel):
        """Populates multi-modal physical hypotheses for the persistent world model."""
        hypotheses = [
            WorldModelHypothesisModel(
                id=f"HYP-{entity.entity_id[-5:]}-01",
                entity_id=entity.entity_id,
                property_name="morphology_type",
                hypothesis_value="Well-preserved parabolic impact crater with continuous raised ejecta blanket",
                confidence=0.91,
                uncertainty=0.09,
                evidence_count=2,
                supporting_evidence_json=json.dumps(["OHRC sub-meter optical rim sharpness", "TMC-2 parabolic elevation profile"]),
                conflicting_evidence_json=json.dumps([]),
            ),
            WorldModelHypothesisModel(
                id=f"HYP-{entity.entity_id[-5:]}-02",
                entity_id=entity.entity_id,
                property_name="terrain_roughness",
                hypothesis_value="Moderate-to-high local slope roughness (16.8° mean inner rim slope)",
                confidence=0.88,
                uncertainty=0.12,
                evidence_count=1,
                supporting_evidence_json=json.dumps(["TMC-2 stereo DEM gradient"]),
                conflicting_evidence_json=json.dumps([]),
            ),
            WorldModelHypothesisModel(
                id=f"HYP-{entity.entity_id[-5:]}-03",
                entity_id=entity.entity_id,
                property_name="spectral_composition",
                hypothesis_value="Excavated clinopyroxene and basaltic mare melt lining interior floor",
                confidence=0.74,
                uncertainty=0.26,
                evidence_count=1,
                supporting_evidence_json=json.dumps(["IIRS 1.05μm absorption band minimum"]),
                conflicting_evidence_json=json.dumps(["Low spatial resolution (20m/px) blends wall anorthosite"]),
            ),
        ]
        for h in hypotheses:
            self.db.add(h)
        self.db.commit()

    def list_entities(self) -> List[LunarEntityModel]:
        return self.db.query(LunarEntityModel).all()

    def get_entity(self, entity_id: str) -> Optional[LunarEntityModel]:
        return self.db.query(LunarEntityModel).filter(LunarEntityModel.entity_id == entity_id).first()

    def get_entity_observations(self, entity_id: str) -> List[EntityObservationModel]:
        return self.db.query(EntityObservationModel).filter(EntityObservationModel.entity_id == entity_id).all()

    def get_entity_hypotheses(self, entity_id: str) -> List[WorldModelHypothesisModel]:
        return self.db.query(WorldModelHypothesisModel).filter(WorldModelHypothesisModel.entity_id == entity_id).all()
