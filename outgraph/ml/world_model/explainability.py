"""World Model Scientific Explainability Engine.
Stage 5.9: Fully Traceable Entity Scientific Justification Cards.

Produces comprehensive, human-interpretable scientific explanation cards for any entity:
- Current lifecycle state
- Supported evidence items with sources
- Contradicting evidence items
- Unknown / unmeasured dimensions
- Blocked factors (e.g. swath non-overlap)
- Physical uncertainty breakdown
- Active knowledge gaps
- Prioritized next-best observations
- Complete provenance trail
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .entity import LunarEntity, EntityState
from .evidence import EntityEvidenceProfile, EvidenceType, EvidenceStatus
from .knowledge_gap import KnowledgeGap
from .next_best_observation import NextBestObservation


class EntityExplanationCard(BaseModel):
    """Traceable scientific justification card for a lunar entity."""
    entity_id: str
    entity_type: str
    lifecycle_state: str
    supported_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    unknown_evidence: List[str] = Field(default_factory=list)
    blocked_factors: List[str] = Field(default_factory=list)
    uncertainty_statement: str
    active_knowledge_gaps: List[str] = Field(default_factory=list)
    recommended_next_observations: List[str] = Field(default_factory=list)
    provenance_summary: Dict[str, Any] = Field(default_factory=dict)
    full_text_report: str

    model_config = {"frozen": False}


class ExplainabilityEngine:
    """Generates rigorous, traceable explanation cards grounded in empirical evidence."""

    @classmethod
    def generate_card(
        cls,
        entity: LunarEntity,
        evidence_profile: Optional[EntityEvidenceProfile] = None,
        gaps: Optional[List[KnowledgeGap]] = None,
        recommendations: Optional[List[NextBestObservation]] = None,
        blocked_factors: Optional[List[str]] = None,
    ) -> EntityExplanationCard:
        """Assembles all scientific facts regarding an entity into a structured explanation card."""
        supp = []
        contra = []
        unknown_dims = []

        if evidence_profile:
            for dim in [EvidenceType.GEOMETRIC, EvidenceType.TERRAIN, EvidenceType.ILLUMINATION, EvidenceType.SPECTRAL, EvidenceType.TEMPORAL]:
                items = evidence_profile.get_by_type(dim)
                if not items:
                    unknown_dims.append(dim.value)
                else:
                    st = evidence_profile.get_status_for_type(dim)
                    if st == EvidenceStatus.SUPPORTED:
                        for ev in items:
                            supp.append(f"{dim.value} ({ev.provenance.source_sensor}): {ev.method}")
                    elif st == EvidenceStatus.CONTRADICTED:
                        for ev in items:
                            contra.append(f"{dim.value} ({ev.provenance.source_sensor}): {ev.notes or 'discrepancy'}")
                    elif st == EvidenceStatus.INSUFFICIENT_EVIDENCE:
                        unknown_dims.append(f"{dim.value} (INSUFFICIENT_EVIDENCE)")
                    else:
                        unknown_dims.append(dim.value)
        else:
            unknown_dims = ["GEOMETRIC", "TERRAIN", "SPECTRAL", "TEMPORAL"]

        # Blocked factors
        blocks = blocked_factors or []
        for assoc in entity.associations:
            if assoc.status.value == "REJECTED" and assoc.rejection_reason:
                blocks.append(f"{assoc.provenance.source_sensor}: {assoc.rejection_reason}")

        # Active gaps
        gap_strs = []
        if gaps:
            for g in gaps:
                gap_strs.append(f"[{g.severity.value}] {g.gap_type.value}: {g.description}")

        # Recommendations
        rec_strs = []
        if recommendations:
            for r in recommendations:
                rec_strs.append(f"Target {r.candidate_sensor}: {r.uncertainty_reduction_basis}")

        # Uncertainty statement
        unc_val = entity.uncertainty_m if entity.uncertainty_m is not None else 0.25
        unc_stmt = f"Localization spatial bound ~{unc_val}m; regional DEM resolution limit 59.2m"

        # Provenance summary
        prov = {
            "created_at": entity.created_at.isoformat(),
            "updated_at": entity.updated_at.isoformat(),
            "associations_count": len(entity.associations),
            "sensors": list({a.provenance.source_sensor for a in entity.associations}),
        }

        # Build formatted report
        lines = [
            f"=== LUNAR WORLD MODEL EXPLANATION CARD: {entity.entity_id} ===",
            f"Entity Type: {entity.entity_type.upper()}",
            f"Coordinates: Lat {entity.latitude:.4f}° N, Lon {entity.longitude:.4f}° E, Elev {entity.elevation_m if entity.elevation_m is not None else 'UNCONSTRAINED'}m",
            f"Lifecycle State: {entity.state.value}",
            "",
            "SUPPORTED EVIDENCE:",
        ]
        lines.extend([f"  + {s}" for s in supp] or ["  (None)"])

        lines.append("\nCONTRADICTING EVIDENCE:")
        lines.extend([f"  - {c}" for c in contra] or ["  (None)"])

        lines.append(f"\nUNKNOWN EVIDENCE: {', '.join(unknown_dims) if unknown_dims else 'None'}")

        lines.append("\nBLOCKED FACTORS:")
        lines.extend([f"  ! {b}" for b in blocks] or ["  (None)"])

        lines.append(f"\nUNCERTAINTY: {unc_stmt}")

        lines.append("\nACTIVE KNOWLEDGE GAPS:")
        lines.extend([f"  * {g}" for g in gap_strs] or ["  (None)"])

        lines.append("\nNEXT-BEST OBSERVATIONS:")
        lines.extend([f"  > {r}" for r in rec_strs] or ["  (None)"])

        full_text = "\n".join(lines)

        return EntityExplanationCard(
            entity_id=entity.entity_id,
            entity_type=entity.entity_type,
            lifecycle_state=entity.state.value,
            supported_evidence=supp,
            contradicting_evidence=contra,
            unknown_evidence=unknown_dims,
            blocked_factors=blocks,
            uncertainty_statement=unc_stmt,
            active_knowledge_gaps=gap_strs,
            recommended_next_observations=rec_strs,
            provenance_summary=prov,
            full_text_report=full_text,
        )
