"""Next-Best Observation API Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.recommendation_service import RecommendationService
from ...schemas.knowledge import RecommendationRequest, RecommendationResponse
from ...models.recommendation import RecommendationModel

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/next-observation", response_model=RecommendationResponse)
def compute_next_observation(
    request: RecommendationRequest, db: Session = Depends(get_db)
):
    """Calculates quantitative Expected Information Gain and returns ranked sensor recommendations."""
    rec_service = RecommendationService(db)
    try:
        rec = rec_service.recommend_next_observation(
            entity_id=request.entity_id,
            scientific_question=request.scientific_question,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ranked = getattr(rec, "ranked_sensors", [])

    return RecommendationResponse(
        id=rec.id,
        entity_id=rec.entity_id,
        scientific_question=rec.scientific_question,
        recommended_sensor=rec.recommended_sensor,
        expected_information_gain=rec.expected_information_gain,
        uncertainty_reduction=rec.uncertainty_reduction,
        feasibility=rec.feasibility,
        explanation=rec.explanation,
        ranked_sensors=ranked,
        created_at=rec.created_at,
    )
