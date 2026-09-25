"""Multimodal Evidence Fusion and Explanation Engine.
Stage 5.3: Provenance-Preserving Evidence Fusion.

Enforces:
1. Rejection of naive score averaging (e.g. confidence = avg(scores)).
2. Individual preservation of all 11 evidence dimensions with their sources and uncertainties.
3. Generation of explicit, structured explanations of supported, contradicted, unknown, and blocked factors.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .entity import LunarEntity, EntityState
from .evidence import EntityEvidenceProfile, EvidenceType, EvidenceStatus, Evidence


class FusedEvidenceExplanation(BaseModel):
    """Structured, explainable synthesis of multi-modal evidence for a lunar entity."""
    entity_id: str
    overall_lifecycle_state: EntityState
    supported_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    contradicted_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    unknown_dimensions: List[str] = Field(default_factory=list)
    insufficient_evidence_dimensions: List[str] = Field(default_factory=list)
    blocked_factors: List[str] = Field(default_factory=list)
    summary_text: str

    model_config = {"frozen": False}


class EvidenceFusionEngine:
    """Fuses multi-modal evidence profiles into transparent, explainable summaries."""

    ALL_DIMENSIONS = [
        EvidenceType.GEOMETRIC,
        EvidenceType.TERRAIN,
        EvidenceType.ILLUMINATION,
        EvidenceType.SPECTRAL,
        EvidenceType.SCALE,
        EvidenceType.TEMPORAL,
        EvidenceType.TEXTURE,
        EvidenceType.REGISTRATION,
        EvidenceType.PHYSICAL,
        EvidenceType.MANUAL,
    ]

    @classmethod
    def fuse_profile(
        cls,
        entity: LunarEntity,
        profile: EntityEvidenceProfile,
        blocked_factors: Optional[List[str]] = None,
    ) -> FusedEvidenceExplanation:
        """Fuses evidence items across all 11 dimensions, preserving provenance and explaining gaps."""
        supported_list = []
        contradicted_list = []
        unknown_dims = []
        insufficient_dims = []

        for dim in cls.ALL_DIMENSIONS:
            items = profile.get_by_type(dim)
            if not items:
                unknown_dims.append(dim.value)
                continue

            dim_status = profile.get_status_for_type(dim)
            if dim_status == EvidenceStatus.SUPPORTED:
                for ev in items:
                    if ev.status == EvidenceStatus.SUPPORTED:
                        supported_list.append({
                            "dimension": dim.value,
                            "sensor": ev.provenance.source_sensor,
                            "measurement": ev.measurement,
                            "uncertainty": ev.uncertainty,
                            "method": ev.method,
                        })
            elif dim_status == EvidenceStatus.CONTRADICTED:
                for ev in items:
                    if ev.status == EvidenceStatus.CONTRADICTED:
                        contradicted_list.append({
                            "dimension": dim.value,
                            "sensor": ev.provenance.source_sensor,
                            "measurement": ev.measurement,
                            "notes": ev.notes,
                        })
            elif dim_status == EvidenceStatus.INSUFFICIENT_EVIDENCE:
                insufficient_dims.append(dim.value)
            else:
                unknown_dims.append(dim.value)

        # Build natural scientific explanation
        lines = [f"Entity {entity.entity_id} ({entity.entity_type.upper()}) Evaluation Summary:"]
        lines.append(f"Lifecycle State: {entity.state.value}")

        if supported_list:
            lines.append("SUPPORTED BY:")
            for s in supported_list:
                lines.append(f"  - {s['dimension']} ({s['sensor']}): {s['method']}")

        if contradicted_list:
            lines.append("CONTRADICTED BY:")
            for c in contradicted_list:
                lines.append(f"  - {c['dimension']} ({c['sensor']}): {c.get('notes', 'measurement conflict')}")

        if unknown_dims:
            lines.append(f"UNKNOWN DIMENSIONS ({len(unknown_dims)}): {', '.join(unknown_dims)}")

        if insufficient_dims:
            lines.append(f"INSUFFICIENT EVIDENCE DIMENSIONS: {', '.join(insufficient_dims)}")

        blocks = blocked_factors or []
        if blocks:
            lines.append("BLOCKED BY:")
            for b in blocks:
                lines.append(f"  - {b}")

        summary = "\n".join(lines)

        return FusedEvidenceExplanation(
            entity_id=entity.entity_id,
            overall_lifecycle_state=entity.state,
            supported_evidence=supported_list,
            contradicted_evidence=contradicted_list,
            unknown_dimensions=unknown_dims,
            insufficient_evidence_dimensions=insufficient_dims,
            blocked_factors=blocks,
            summary_text=summary,
        )
