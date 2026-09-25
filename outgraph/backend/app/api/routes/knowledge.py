from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.knowledge_gap_service import KnowledgeGapService
from ...schemas.knowledge import KnowledgeGapResponse
from ...models.recommendation import KnowledgeGapModel

router = APIRouter(prefix="/knowledge-gaps", tags=["Knowledge Gaps"])

SUPPORTED_GAP_TYPES = [
    "MISSING_MODALITY",
    "MISSING_TEMPORAL_OBSERVATION",
    "MISSING_GEOMETRIC_VALIDATION",
    "MISSING_TERRAIN_VALIDATION",
    "MISSING_SPECTRAL_VALIDATION",
    "INSUFFICIENT_CORRESPONDENCE",
    "FOOTPRINT_NON_OVERLAP",
    "UNCERTAINTY_TOO_HIGH",
]


@router.get("/types")
def get_supported_gap_types() -> Dict[str, Any]:
    """Returns the 8 epistemic knowledge gap taxonomies supported by the Lunar World Model."""
    return {
        "supported_gap_types": SUPPORTED_GAP_TYPES,
        "description": "Epistemic uncertainty taxonomies driving next-best observation targeting.",
    }


@router.get("", response_model=List[KnowledgeGapResponse])
def get_knowledge_gaps(db: Session = Depends(get_db)):
    """Retrieves prioritized list of scientific blind spots."""
    gap_service = KnowledgeGapService(db)
    gaps = gap_service.list_gaps()
    return [
        KnowledgeGapResponse(
            id=g.id,
            entity_id=g.entity_id,
            gap_type=g.gap_type,
            severity=g.severity,
            reason=g.reason,
            recommended_sensor=g.recommended_sensor,
            status=g.status,
            is_synthetic=g.is_synthetic,
            created_at=g.created_at,
        )
        for g in gaps
    ]


@router.get("/{gap_id}", response_model=KnowledgeGapResponse)
def get_knowledge_gap_by_id(gap_id: str, db: Session = Depends(get_db)):
    """Retrieves a specific knowledge gap by ID."""
    gap = db.query(KnowledgeGapModel).filter(KnowledgeGapModel.id == gap_id).first()
    if not gap:
        raise HTTPException(status_code=404, detail=f"Knowledge gap '{gap_id}' not found")

    return KnowledgeGapResponse(
        id=gap.id,
        entity_id=gap.entity_id,
        gap_type=gap.gap_type,
        severity=gap.severity,
        reason=gap.reason,
        recommended_sensor=gap.recommended_sensor,
        status=gap.status,
        is_synthetic=gap.is_synthetic,
        created_at=gap.created_at,
    )

