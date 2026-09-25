"""Knowledge-Gap Detection Engine for Lunar World Model.
Stage 4.5: Evidence-Driven Epistemic Blind Spot Identification.

Identifies what the world model does NOT know:
- Missing modalities (e.g. IIRS spectral composition)
- Missing terrain elevation confirmation
- Footprint non-overlap across sensor swaths (Phase 3 finding)
- Temporal evolution gaps
- Excessive spatial or measurement uncertainty
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid
from pydantic import BaseModel, Field

from .entity import LunarEntity, AssociationStatus, AssociationType
from .evidence import EntityEvidenceProfile, EvidenceType, EvidenceStatus


class GapType(str, Enum):
    """Categorical types of scientific knowledge gaps."""
    MISSING_MODALITY = "MISSING_MODALITY"
    MISSING_TEMPORAL_OBSERVATION = "MISSING_TEMPORAL_OBSERVATION"
    MISSING_GEOMETRIC_VALIDATION = "MISSING_GEOMETRIC_VALIDATION"
    MISSING_TERRAIN_VALIDATION = "MISSING_TERRAIN_VALIDATION"
    MISSING_SPECTRAL_VALIDATION = "MISSING_SPECTRAL_VALIDATION"
    INSUFFICIENT_CORRESPONDENCE = "INSUFFICIENT_CORRESPONDENCE"
    FOOTPRINT_NON_OVERLAP = "FOOTPRINT_NON_OVERLAP"
    UNCERTAINTY_TOO_HIGH = "UNCERTAINTY_TOO_HIGH"


class GapSeverity(str, Enum):
    """Scientific impact of a knowledge gap."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class GapStatus(str, Enum):
    """Operational status of a knowledge gap."""
    OPEN = "OPEN"
    RESOLVED = "RESOLVED"
    BLOCKED = "BLOCKED"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class KnowledgeGap(BaseModel):
    """Explicit, structured scientific blind spot."""
    gap_id: str = Field(default_factory=lambda: f"GAP-{uuid.uuid4().hex[:8].upper()}")
    entity_id: str
    gap_type: GapType
    description: str
    required_evidence: List[str] = Field(default_factory=list)
    current_evidence: List[str] = Field(default_factory=list)
    severity: GapSeverity = GapSeverity.MEDIUM
    blocking_reason: Optional[str] = None
    provenance: Dict[str, Any] = Field(default_factory=dict)
    status: GapStatus = GapStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": False}


class KnowledgeGapDetector:
    """Detects and generates explicit knowledge gaps for lunar entities."""

    def __init__(self, uncertainty_threshold_m: float = 50.0):
        self.uncertainty_threshold_m = uncertainty_threshold_m

    def detect_gaps(
        self,
        entity: LunarEntity,
        evidence_profile: Optional[EntityEvidenceProfile] = None,
        rejection_events: Optional[List[Dict[str, Any]]] = None,
    ) -> List[KnowledgeGap]:
        """Scans entity associations, evidence profiles, and geometry rejection events to identify gaps."""
        gaps: List[KnowledgeGap] = []
        sensors_present = {a.provenance.source_sensor for a in entity.associations if a.status == AssociationStatus.SUPPORTED}

        # 1. Footprint Non-Overlap Gaps (Preserves Phase 3 Rejection Finding)
        if rejection_events:
            for rev in rejection_events:
                reason = rev.get("rejection_reason", "")
                if "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH" in reason or "FOOTPRINT" in reason or "SPATIAL_DISTANCE" in reason:
                    gaps.append(
                        KnowledgeGap(
                            gap_id=f"GAP-{entity.entity_id[-6:]}-NONOVERLAP",
                            entity_id=entity.entity_id,
                            gap_type=GapType.FOOTPRINT_NON_OVERLAP,
                            description="Calibrated sensor footprints do not physically overlap on lunar surface.",
                            required_evidence=["Overlapping swath or contiguous mosaic coverage"],
                            current_evidence=[f"Footprints disjoint; rejection reason: {reason}"],
                            severity=GapSeverity.HIGH,
                            blocking_reason="PHYSICAL_FOOTPRINT_SEPARATION",
                            provenance={"source_event": rev},
                        )
                    )

        # 2. Check Missing Spectral Validation (IIRS)
        has_spectral = False
        if evidence_profile:
            spectral_items = evidence_profile.get_by_type(EvidenceType.SPECTRAL)
            has_spectral = any(ev.status == EvidenceStatus.SUPPORTED for ev in spectral_items)
        if not has_spectral and "IIRS" not in sensors_present:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-SPECTRAL",
                    entity_id=entity.entity_id,
                    gap_type=GapType.MISSING_SPECTRAL_VALIDATION,
                    description="Entity lacks hyperspectral (IIRS) coverage to resolve mineralogy (pyroxene/olivine absorption bands).",
                    required_evidence=["IIRS 0.8-5.0um reflectance cube"],
                    current_evidence=list(sensors_present),
                    severity=GapSeverity.HIGH,
                    blocking_reason="NO_SPECTRAL_DATA_ATTACHED",
                    provenance={"checked_evidence": "SPECTRAL"},
                )
            )

        # 3. Check Missing Terrain Elevation Confirmation (SLDEM / TMC-2)
        has_terrain = False
        if evidence_profile:
            terrain_items = evidence_profile.get_by_type(EvidenceType.TERRAIN)
            has_terrain = any(ev.status == EvidenceStatus.SUPPORTED for ev in terrain_items)
        if not has_terrain and entity.elevation_m is None:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-TERRAIN",
                    entity_id=entity.entity_id,
                    gap_type=GapType.MISSING_TERRAIN_VALIDATION,
                    description="Entity lacks 3D topographic confirmation from DEM or stereo photogrammetry.",
                    required_evidence=["SLDEM2015 elevation or TMC-2 stereo profile"],
                    current_evidence=list(sensors_present),
                    severity=GapSeverity.MEDIUM,
                    provenance={"checked_evidence": "TERRAIN"},
                )
            )

        # 4. Check Temporal Observation Gap
        temporal_assocs = [a for a in entity.associations if a.association_type == AssociationType.TEMPORAL or a.status == AssociationStatus.SUPPORTED]
        if len(temporal_assocs) < 2:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-TEMPORAL",
                    entity_id=entity.entity_id,
                    gap_type=GapType.MISSING_TEMPORAL_OBSERVATION,
                    description="Observed at only a single epoch. Temporal evolution, impact crater degradation, and variable illumination unconstrained.",
                    required_evidence=["Multi-epoch observations at varying solar azimuth"],
                    current_evidence=[f"{len(temporal_assocs)} observation(s) recorded"],
                    severity=GapSeverity.LOW,
                    provenance={"association_count": len(temporal_assocs)},
                )
            )

        # 5. Check Uncertainty Exceeds Threshold
        if entity.uncertainty_m is not None and entity.uncertainty_m > self.uncertainty_threshold_m:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-HIGH-UNC",
                    entity_id=entity.entity_id,
                    gap_type=GapType.UNCERTAINTY_TOO_HIGH,
                    description=f"Spatial/elevation uncertainty ({entity.uncertainty_m:.1f}m) exceeds scientific tolerance ({self.uncertainty_threshold_m:.1f}m).",
                    required_evidence=["Sub-meter optical targeting or high-resolution DEM sampling"],
                    current_evidence=[f"Current uncertainty: {entity.uncertainty_m:.1f}m"],
                    severity=GapSeverity.HIGH,
                    provenance={"uncertainty_m": entity.uncertainty_m},
                )
            )

        # 6. Check Insufficient Correspondence
        if len(entity.associations) == 1 and entity.associations[0].status == AssociationStatus.SUPPORTED:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-INSUFF-CORR",
                    entity_id=entity.entity_id,
                    gap_type=GapType.INSUFFICIENT_CORRESPONDENCE,
                    description="Feature confirmed by only one observation. Lacks cross-sensor physical correspondence.",
                    required_evidence=["Independent cross-sensor observation"],
                    current_evidence=[f"Single sensor: {list(sensors_present)}"],
                    severity=GapSeverity.MEDIUM,
                    provenance={"sensor_count": len(sensors_present)},
                )
            )

        # 7. Check Missing Geometric Validation
        has_geom = False
        if evidence_profile:
            geom_items = evidence_profile.get_by_type(EvidenceType.GEOMETRIC)
            has_geom = any(ev.status == EvidenceStatus.SUPPORTED for ev in geom_items)
        if evidence_profile is not None and not has_geom:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-GEOM",
                    entity_id=entity.entity_id,
                    gap_type=GapType.MISSING_GEOMETRIC_VALIDATION,
                    description="Entity lacks verified geometric inlier consensus / reprojection validation.",
                    required_evidence=["Geometric RANSAC / homography consensus"],
                    severity=GapSeverity.HIGH,
                    provenance={"checked_evidence": "GEOMETRIC"},
                )
            )

        # 8. Check Missing Modality
        if evidence_profile is not None and not has_spectral:
            gaps.append(
                KnowledgeGap(
                    gap_id=f"GAP-{entity.entity_id[-6:]}-MODALITY",
                    entity_id=entity.entity_id,
                    gap_type=GapType.MISSING_MODALITY,
                    description="Entity lacks multi-modal sensory coverage beyond nominal optical channel.",
                    required_evidence=["Multi-spectral or altimetry channel"],
                    severity=GapSeverity.MEDIUM,
                    provenance={"checked_evidence": "MODALITY"},
                )
            )

        return gaps
