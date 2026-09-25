"""Knowledge-Gap Detection Service.
Identifies missing modalities, illumination gaps, and high epistemic uncertainty in the Lunar World Model.
"""

import uuid
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..models.lunar_entity import LunarEntityModel, EntityObservationModel, WorldModelHypothesisModel
from ..models.recommendation import KnowledgeGapModel


class KnowledgeGapService:
    """Detects and prioritizes scientific blind spots across lunar regions."""

    def __init__(self, db: Session):
        self.db = db

    def scan_knowledge_gaps(self) -> List[KnowledgeGapModel]:
        """Analyzes all entities and creates/updates prioritized knowledge gaps."""
        entities = self.db.query(LunarEntityModel).all()
        detected_gaps: List[KnowledgeGapModel] = []

        for entity in entities:
            # Check attached sensor observations
            obs_rels = (
                self.db.query(EntityObservationModel)
                .filter(EntityObservationModel.entity_id == entity.entity_id)
                .all()
            )
            sensors_present = {r.sensor_type for r in obs_rels}

            # 1. Check Missing Spectral Modality (IIRS)
            if "IIRS" not in sensors_present:
                gap_id = f"GAP-{entity.entity_id[-5:]}-SPECTRAL"
                existing = self.db.query(KnowledgeGapModel).filter(KnowledgeGapModel.id == gap_id).first()
                if not existing:
                    gap = KnowledgeGapModel(
                        id=gap_id,
                        entity_id=entity.entity_id,
                        gap_type="MISSING_SPECTRAL_EVIDENCE",
                        severity="HIGH",
                        reason=f"High-resolution morphology and terrain elevation profiles are registered, but no hyperspectral IIRS data is attached to determine mineral composition (pyroxene/olivine absorption bands).",
                        recommended_sensor="IIRS",
                        status="OPEN",
                        is_synthetic=bool(entity.is_synthetic),
                    )
                    self.db.add(gap)
                    detected_gaps.append(gap)
                else:
                    detected_gaps.append(existing)

            # 2. Check Illumination Uncertainty / Shadow Diversity
            if len(obs_rels) < 2:
                gap_id = f"GAP-{entity.entity_id[-5:]}-ILLUM"
                existing = self.db.query(KnowledgeGapModel).filter(KnowledgeGapModel.id == gap_id).first()
                if not existing:
                    gap = KnowledgeGapModel(
                        id=gap_id,
                        entity_id=entity.entity_id,
                        gap_type="HIGH_ILLUMINATION_UNCERTAINTY",
                        severity="MEDIUM",
                        reason="Observation acquired under single solar azimuth angle. Lacks orthogonal or opposite illumination to resolve interior permanent shadow boundaries.",
                        recommended_sensor="OHRC",
                        status="OPEN",
                        is_synthetic=bool(entity.is_synthetic),
                    )
                    self.db.add(gap)
                    detected_gaps.append(gap)
                else:
                    detected_gaps.append(existing)

            # 3. Check Stereo DEM Resolution (TMC-2)
            if "TMC-2" not in sensors_present:
                gap_id = f"GAP-{entity.entity_id[-5:]}-TERRAIN"
                existing = self.db.query(KnowledgeGapModel).filter(KnowledgeGapModel.id == gap_id).first()
                if not existing:
                    gap = KnowledgeGapModel(
                        id=gap_id,
                        entity_id=entity.entity_id,
                        gap_type="UNVERIFIED_TERRAIN_RELATION",
                        severity="MEDIUM",
                        reason="Lacks 3D stereo photogrammetric DEM coverage from TMC-2. Vertical depth and true slope cannot be independently cross-verified.",
                        recommended_sensor="TMC-2",
                        status="OPEN",
                        is_synthetic=bool(entity.is_synthetic),
                    )
                    self.db.add(gap)
                    detected_gaps.append(gap)
                else:
                    detected_gaps.append(existing)

        self.db.commit()
        return self.db.query(KnowledgeGapModel).all()

    def list_gaps(self) -> List[KnowledgeGapModel]:
        gaps = self.db.query(KnowledgeGapModel).all()
        if not gaps:
            return self.scan_knowledge_gaps()
        return gaps
