"""Knowledge Gap API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.knowledge_gap_service import KnowledgeGapService
from ...schemas.knowledge import KnowledgeGapResponse

router = APIRouter(prefix="/knowledge-gaps", tags=["Knowledge Gaps"])


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
            created_at=g.created_at,
        )
        for g in gaps
    ]
