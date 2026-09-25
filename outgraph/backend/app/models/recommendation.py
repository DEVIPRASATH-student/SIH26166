"""Knowledge Gaps and Next-Best Observation Recommendation Models."""

from datetime import datetime
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, ForeignKey
from ..database.session import Base


class KnowledgeGapModel(Base):
    __tablename__ = "knowledge_gaps"

    id = Column(String(64), primary_key=True, index=True)
    entity_id = Column(String(64), ForeignKey("lunar_entities.entity_id"), nullable=False, index=True)
    gap_type = Column(String(64), nullable=False)  # MISSING_SPECTRAL_EVIDENCE, HIGH_ILLUMINATION_UNCERTAINTY, etc.
    severity = Column(String(16), default="MEDIUM")  # HIGH, MEDIUM, LOW

    reason = Column(Text, nullable=False)
    recommended_sensor = Column(String(32), default="IIRS")
    status = Column(String(32), default="OPEN")  # OPEN, RESOLVED, SCHEDULED
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id = Column(String(64), primary_key=True, index=True)
    entity_id = Column(String(64), ForeignKey("lunar_entities.entity_id"), nullable=False, index=True)
    scientific_question = Column(String(128), default="spectral analysis")

    recommended_sensor = Column(String(32), nullable=False)  # OHRC, TMC-2, IIRS
    expected_information_gain = Column(Float, nullable=False)
    uncertainty_reduction = Column(Float, default=0.35)
    feasibility = Column(Float, default=0.90)

    explanation = Column(Text, nullable=False)
    is_synthetic = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
