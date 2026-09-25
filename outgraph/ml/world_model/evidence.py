"""Multimodal Evidence Model for Lunar World Model.
Stage 4.2: Structured Multimodal Evidence Representation.

Distinguishes UNKNOWN, INSUFFICIENT_EVIDENCE, CONTRADICTED, and REJECTED states.
Supports all 11 scientific evidence types with provenance and uncertainty preservation.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import uuid
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    """Scientific modality/dimension of lunar evidence."""
    GEOMETRIC = "GEOMETRIC"
    TERRAIN = "TERRAIN"
    ILLUMINATION = "ILLUMINATION"
    SPECTRAL = "SPECTRAL"
    SCALE = "SCALE"
    TEMPORAL = "TEMPORAL"
    TEXTURE = "TEXTURE"
    REGISTRATION = "REGISTRATION"
    PHYSICAL = "PHYSICAL"
    MANUAL = "MANUAL"
    SYNTHETIC = "SYNTHETIC"


class EvidenceStatus(str, Enum):
    """Evaluation status of evidence. Crucially distinguishes UNKNOWN vs INSUFFICIENT_EVIDENCE vs CONTRADICTED vs REJECTED."""
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    UNVALIDATED = "UNVALIDATED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REJECTED = "REJECTED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class EvidenceProvenance(BaseModel):
    """Provenance tracking for individual evidence items."""
    source_sensor: str
    source_product_id: Optional[str] = None
    source_processing_stage: str = "PHASE4_STAGE2_EVIDENCE"
    source_method: str = "DIRECT_SENSOR_EXTRACTION"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class Evidence(BaseModel):
    """Individual structured multimodal evidence item."""
    evidence_id: str = Field(default_factory=lambda: f"EV-{uuid.uuid4().hex[:8].upper()}")
    entity_id: str
    observation_id: Optional[str] = None
    evidence_type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.UNKNOWN

    # Quantitative or qualitative measurement
    measurement: Optional[Any] = None
    unit: Optional[str] = None

    # Uncertainty representation (scalar, bound, or description)
    uncertainty: Optional[Union[float, Dict[str, Any], str]] = None
    method: str = "MEASUREMENT"
    source: str = "SENSOR_PAYLOAD"
    is_synthetic: bool = False

    provenance: EvidenceProvenance
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": False}


class EntityEvidenceProfile(BaseModel):
    """Aggregated multi-modal evidence profile for a persistent lunar entity."""
    entity_id: str
    evidence_items: List[Evidence] = Field(default_factory=list)

    def add_or_update(self, item: Evidence) -> None:
        """Adds or updates an evidence item by evidence_id or (evidence_type, observation_id)."""
        existing = None
        for ev in self.evidence_items:
            if ev.evidence_id == item.evidence_id:
                existing = ev
                break
            elif ev.evidence_type == item.evidence_type and ev.observation_id == item.observation_id and ev.observation_id is not None:
                existing = ev
                break

        if existing:
            idx = self.evidence_items.index(existing)
            item.updated_at = datetime.utcnow()
            self.evidence_items[idx] = item
        else:
            self.evidence_items.append(item)

    def get_by_type(self, evidence_type: EvidenceType) -> List[Evidence]:
        """Returns all evidence items of a specified type."""
        return [ev for ev in self.evidence_items if ev.evidence_type == evidence_type]

    def get_status_for_type(self, evidence_type: EvidenceType) -> EvidenceStatus:
        """Summarizes evidence status for a specific evidence dimension."""
        items = self.get_by_type(evidence_type)
        if not items:
            return EvidenceStatus.UNKNOWN

        statuses = {ev.status for ev in items}
        if EvidenceStatus.CONTRADICTED in statuses:
            return EvidenceStatus.CONTRADICTED
        if EvidenceStatus.REJECTED in statuses and not (EvidenceStatus.SUPPORTED in statuses):
            return EvidenceStatus.REJECTED
        if EvidenceStatus.SUPPORTED in statuses:
            return EvidenceStatus.SUPPORTED
        if EvidenceStatus.INSUFFICIENT_EVIDENCE in statuses:
            return EvidenceStatus.INSUFFICIENT_EVIDENCE
        if EvidenceStatus.UNVALIDATED in statuses:
            return EvidenceStatus.UNVALIDATED
        return EvidenceStatus.UNKNOWN

    def has_contradiction(self) -> bool:
        """Detects whether contradictory evidence exists across any modality."""
        for ev in self.evidence_items:
            if ev.status == EvidenceStatus.CONTRADICTED:
                return True
        return False
