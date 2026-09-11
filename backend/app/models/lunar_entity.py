"""Persistent Lunar Entity and World Model Models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, Text, ForeignKey
from ..database.session import Base


class LunarEntityModel(Base):
    __tablename__ = "lunar_entities"

    entity_id = Column(String(64), primary_key=True, index=True)  # e.g., LUNAR-ENTITY-7F91A
    entity_type = Column(String(32), default="crater", index=True)  # crater, boulder, terrain_region, ridge
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    spatial_extent_m = Column(Float, default=150.0)

    confidence = Column(Float, default=0.90)
    uncertainty = Column(Float, default=0.10)

    morphology_json = Column(Text, default="{}")
    elevation_json = Column(Text, default="{}")
    spectral_json = Column(Text, default="{}")

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EntityObservationModel(Base):
    __tablename__ = "entity_observations"

    id = Column(String(64), primary_key=True, index=True)
    entity_id = Column(String(64), ForeignKey("lunar_entities.entity_id"), nullable=False, index=True)
    observation_id = Column(String(64), ForeignKey("observations.id"), nullable=False, index=True)
    correspondence_id = Column(String(64), ForeignKey("correspondences.id"), nullable=True)

    sensor_type = Column(String(32), nullable=False)
    attached_at = Column(DateTime, default=datetime.utcnow)
    confidence = Column(Float, default=0.90)


class WorldModelHypothesisModel(Base):
    __tablename__ = "world_model_hypotheses"

    id = Column(String(64), primary_key=True, index=True)
    entity_id = Column(String(64), ForeignKey("lunar_entities.entity_id"), nullable=False, index=True)
    property_name = Column(String(64), nullable=False)  # terrain_type, mineral_composition, surface_roughness
    hypothesis_value = Column(String(128), nullable=False)

    confidence = Column(Float, default=0.85)
    uncertainty = Column(Float, default=0.15)
    evidence_count = Column(Integer, default=1)

    supporting_evidence_json = Column(Text, default="[]")
    conflicting_evidence_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.utcnow)
