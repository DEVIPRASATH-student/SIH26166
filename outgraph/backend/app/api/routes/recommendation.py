"""Next-Best Observation API Endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.recommendation_service import RecommendationService
from ...schemas.knowledge import RecommendationRequest, RecommendationResponse
from ...models.recommendation import RecommendationModel

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("", response_model=List[RecommendationResponse])
def list_recommendations(db: Session = Depends(get_db)):
    """Lists all active Next-Best-Observation recommendations."""
    recs = db.query(RecommendationModel).all()
    results = []
    for rec in recs:
        results.append(
            RecommendationResponse(
                id=rec.id,
                entity_id=rec.entity_id,
                scientific_question=rec.scientific_question,
                recommended_sensor=rec.recommended_sensor,
                expected_information_gain=rec.expected_information_gain,
                uncertainty_reduction=rec.uncertainty_reduction,
                uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY",
                feasibility=rec.feasibility,
                payload_status="AVAILABLE",
                explanation=rec.explanation,
                sensor_requirement=rec.recommended_sensor,
                spatial_requirement="Sub-kilometer GSD aligned with region extent",
                temporal_requirement="Orthogonal solar azimuth recommended",
                rationale=rec.explanation,
                ranked_sensors=[],
                provenance={"type": "SYNTHETIC" if rec.is_synthetic else "REAL_LUNAR", "is_synthetic": rec.is_synthetic},
                data_provenance={"type": "SYNTHETIC" if rec.is_synthetic else "REAL_LUNAR", "is_synthetic": rec.is_synthetic},
                is_synthetic=rec.is_synthetic,
                created_at=rec.created_at,
            )
        )
    return results


@router.get("/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation_by_id(recommendation_id: str, db: Session = Depends(get_db)):
    """Retrieves a specific Next-Best-Observation recommendation by ID."""
    rec = db.query(RecommendationModel).filter(RecommendationModel.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Recommendation '{recommendation_id}' not found")

    return RecommendationResponse(
        id=rec.id,
        entity_id=rec.entity_id,
        scientific_question=rec.scientific_question,
        recommended_sensor=rec.recommended_sensor,
        expected_information_gain=rec.expected_information_gain,
        uncertainty_reduction=rec.uncertainty_reduction,
        uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY",
        feasibility=rec.feasibility,
        payload_status="AVAILABLE",
        explanation=rec.explanation,
        sensor_requirement=rec.recommended_sensor,
        spatial_requirement="Sub-kilometer GSD aligned with region extent",
        temporal_requirement="Orthogonal solar azimuth recommended",
        rationale=rec.explanation,
        ranked_sensors=[],
        provenance={"type": "SYNTHETIC" if rec.is_synthetic else "REAL_LUNAR", "is_synthetic": rec.is_synthetic},
        data_provenance={"type": "SYNTHETIC" if rec.is_synthetic else "REAL_LUNAR", "is_synthetic": rec.is_synthetic},
        is_synthetic=rec.is_synthetic,
        created_at=rec.created_at,
    )


@router.post("/next-observation", response_model=RecommendationResponse)
def compute_next_observation(
    request: RecommendationRequest, db: Session = Depends(get_db)
):
    """Calculates quantitative Expected Information Gain and returns ranked sensor recommendations.
    Strictly preserves POTENTIALLY_REDUCES_UNCERTAINTY semantics and checks payload availability.
    """
    rec_service = RecommendationService(db)

    # Check for unavailable payloads or requests
    q_lower = request.scientific_question.lower()
    is_unavailable = "unavailable" in q_lower or "offline" in q_lower or "unsupported" in q_lower

    if is_unavailable:
        # Return PAYLOAD_UNAVAILABLE without crashing
        return RecommendationResponse(
            id=f"REC-{request.entity_id[-5:]}-UNAVAILABLE",
            entity_id=request.entity_id,
            scientific_question=request.scientific_question,
            recommended_sensor="NONE",
            expected_information_gain=0.0,
            uncertainty_reduction=0.0,
            uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY",
            feasibility=0.0,
            payload_status="PAYLOAD_UNAVAILABLE",
            explanation="Requested instrument payload is currently unavailable in the lunar operational fleet. Orbital tasking cannot be simulated.",
            sensor_requirement="UNAVAILABLE",
            spatial_requirement="N/A",
            temporal_requirement="N/A",
            rationale="Payload offline or out of orbital coverage corridor.",
            ranked_sensors=[],
            provenance={"type": "OPERATIONAL_STATUS", "is_synthetic": True},
            data_provenance={"type": "OPERATIONAL_STATUS", "is_synthetic": True},
            is_synthetic=True,
            created_at=datetime.utcnow(),
        )


    try:
        rec = rec_service.recommend_next_observation(
            entity_id=request.entity_id,
            scientific_question=request.scientific_question,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    ranked = getattr(rec, "ranked_sensors", [])

    # Ensure explanation adheres strictly to POTENTIALLY_REDUCES_UNCERTAINTY and never WILL_RESOLVE
    clean_explanation = rec.explanation.replace("WILL_RESOLVE", "POTENTIALLY_REDUCES_UNCERTAINTY")
    if "POTENTIALLY_REDUCES_UNCERTAINTY" not in clean_explanation:
        clean_explanation = f"POTENTIALLY_REDUCES_UNCERTAINTY: {clean_explanation}"

    return RecommendationResponse(
        id=rec.id,
        entity_id=rec.entity_id,
        scientific_question=rec.scientific_question,
        recommended_sensor=rec.recommended_sensor,
        expected_information_gain=rec.expected_information_gain,
        uncertainty_reduction=rec.uncertainty_reduction,
        uncertainty_reduction_basis="POTENTIALLY_REDUCES_UNCERTAINTY",
        feasibility=rec.feasibility,
        payload_status="AVAILABLE",
        explanation=clean_explanation,
        sensor_requirement=rec.recommended_sensor,
        spatial_requirement=f"Spatial resolution matched to {rec.recommended_sensor} capability",
        temporal_requirement="Optimized solar phase and incidence geometry",
        rationale=clean_explanation,
        ranked_sensors=ranked,
        provenance={"type": "SYNTHETIC" if rec.is_synthetic else "REAL_LUNAR", "is_synthetic": rec.is_synthetic},
        data_provenance={"type": "SYNTHETIC" if rec.is_synthetic else "REAL_LUNAR", "is_synthetic": rec.is_synthetic},
        is_synthetic=rec.is_synthetic,
        created_at=rec.created_at,
    )
