"""Cross-Sensor Entity Validation Engine.
Stage 5.2: Multi-Modal Entity Lifecycle and Cross-Sensor Validation.

Enforces:
1. 'Two observations' does NOT automatically mean CONFIRMED.
2. Confirmation strictly requires independent evidence, spatial consistency, compatible geometry, and no contradictions.
3. Explicit handling of:
   - Case A: Compatible overlap with independent evidence -> CONFIRMED
   - Case B: Geographically close but physically incompatible -> REJECTED / INSUFFICIENT_EVIDENCE
   - Case C: Contradictory physical measurements -> CONTRADICTED
   - Case D: Single observation -> CANDIDATE / SUPPORTED (never prematurely confirmed)
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

from .entity import LunarEntity, EntityState, EntityAssociation, AssociationStatus, AssociationType
from .evidence import EntityEvidenceProfile, EvidenceType, EvidenceStatus


class ValidationCaseResult(BaseModel):
    """Result of cross-sensor entity lifecycle evaluation."""
    entity_id: str
    evaluated_case: str
    resulting_state: EntityState
    is_confirmed: bool
    explanation: str
    blocking_factors: List[str] = Field(default_factory=list)


class CrossSensorEntityValidator:
    """Validates persistent lunar entities across multiple sensor observations."""

    @staticmethod
    def evaluate_lifecycle(
        entity: LunarEntity,
        evidence_profile: Optional[EntityEvidenceProfile] = None,
    ) -> ValidationCaseResult:
        """Determines the exact physical lifecycle state of a lunar entity."""
        supported_assocs = [a for a in entity.associations if a.status == AssociationStatus.SUPPORTED]
        rejected_assocs = [a for a in entity.associations if a.status == AssociationStatus.REJECTED]
        contradicted_assocs = [a for a in entity.associations if a.status == AssociationStatus.CONTRADICTED]

        # Check for contradictions in evidence or associations
        has_evidence_contradiction = evidence_profile.has_contradiction() if evidence_profile else False

        # Case C: Contradictory Physical Evidence
        if contradicted_assocs or has_evidence_contradiction:
            entity.state = EntityState.CONTRADICTED
            return ValidationCaseResult(
                entity_id=entity.entity_id,
                evaluated_case="CASE_C_CONTRADICTORY_EVIDENCE",
                resulting_state=EntityState.CONTRADICTED,
                is_confirmed=False,
                explanation="Entity state set to CONTRADICTED due to conflicting physical or geometric evidence.",
                blocking_factors=["Evidence conflict across independent sensor observations."],
            )

        # Case B: Incompatible or Rejected Associations
        if rejected_assocs and not supported_assocs:
            entity.state = EntityState.REJECTED
            reasons = [a.rejection_reason or "UNKNOWN_REJECTION" for a in rejected_assocs]
            return ValidationCaseResult(
                entity_id=entity.entity_id,
                evaluated_case="CASE_B_PHYSICALLY_INCOMPATIBLE",
                resulting_state=EntityState.REJECTED,
                is_confirmed=False,
                explanation="Entity rejected: all candidate associations failed physical, geometric, or footprint checks.",
                blocking_factors=reasons,
            )

        # Case D: Single Observation
        if len(supported_assocs) == 1:
            entity.state = EntityState.SUPPORTED
            return ValidationCaseResult(
                entity_id=entity.entity_id,
                evaluated_case="CASE_D_SINGLE_OBSERVATION",
                resulting_state=EntityState.SUPPORTED,
                is_confirmed=False,
                explanation="Entity supported by a single observation; cannot be confirmed without independent cross-sensor verification.",
                blocking_factors=["Lacks independent multi-sensor corroboration."],
            )

        # Case A: Multiple Compatible Observations
        if len(supported_assocs) >= 2:
            # Check sensor independence
            sensors = {a.provenance.source_sensor for a in supported_assocs}
            if len(sensors) >= 2:
                # Multiple distinct sensors corroborate the entity
                entity.state = EntityState.CONFIRMED
                return ValidationCaseResult(
                    entity_id=entity.entity_id,
                    evaluated_case="CASE_A_COMPATIBLE_OVERLAP",
                    resulting_state=EntityState.CONFIRMED,
                    is_confirmed=True,
                    explanation=f"Entity CONFIRMED: Independently corroborated across distinct sensors: {sorted(list(sensors))}.",
                )
            else:
                # Multiple observations, but same sensor payload
                entity.state = EntityState.SUPPORTED
                return ValidationCaseResult(
                    entity_id=entity.entity_id,
                    evaluated_case="CASE_A_MONO_SENSOR_MULTIPLE_ACQUISITIONS",
                    resulting_state=EntityState.SUPPORTED,
                    is_confirmed=False,
                    explanation=f"Entity supported by multiple acquisitions of the same sensor ({list(sensors)[0]}), but lacks multi-modal cross-sensor confirmation.",
                    blocking_factors=["Requires distinct sensor payload for multi-modal confirmation."],
                )

        # Default fallback
        entity.state = EntityState.CANDIDATE
        return ValidationCaseResult(
            entity_id=entity.entity_id,
            evaluated_case="CASE_DEFAULT_CANDIDATE",
            resulting_state=EntityState.CANDIDATE,
            is_confirmed=False,
            explanation="Entity remains in preliminary CANDIDATE state; insufficient evidence for support.",
            blocking_factors=["No supported observations registered."],
        )
