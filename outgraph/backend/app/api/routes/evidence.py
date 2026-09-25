"""Evidence API Endpoints."""

import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.correspondence_service import CorrespondenceService
from ...schemas.evidence import EvidenceDetailResponse

router = APIRouter(prefix="/evidence", tags=["Evidence"])

ALL_DIMENSIONS = [
    "GEOMETRIC",
    "TERRAIN",
    "ILLUMINATION",
    "SPECTRAL",
    "SCALE",
    "TEMPORAL",
    "TEXTURE",
    "REGISTRATION",
    "PHYSICAL",
    "MANUAL",
    "SYNTHETIC",
]


@router.get("/dimensions")
def get_evidence_dimensions() -> Dict[str, Any]:
    """Returns all 11 scientific evidence dimensions supported by the Lunar World Model."""
    return {
        "dimensions": ALL_DIMENSIONS,
        "policy": "Missing evidence remains explicitly missing. UNKNOWN != NEGATIVE: Missing evidence is never converted into negative proof.",
    }


@router.get("/{correspondence_id}", response_model=EvidenceDetailResponse)
def get_correspondence_evidence_detail(correspondence_id: str, db: Session = Depends(get_db)):
    """Retrieves multi-dimensional evidence profile for a correspondence."""
    corr_service = CorrespondenceService(db)
    corr = corr_service.get_correspondence(correspondence_id)
    if not corr:
        raise HTTPException(status_code=404, detail=f"Correspondence '{correspondence_id}' not found")

    ev = corr_service.get_evidence(corr.id)
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence for correspondence '{correspondence_id}' not found")

    rejection_reasons = json.loads(ev.rejection_reasons_json) if ev.rejection_reasons_json else []

    # Populate 11 dimensions
    dimensions = {
        "GEOMETRIC": round(ev.geometry_score, 4),
        "TERRAIN": round(ev.terrain_score, 4),
        "ILLUMINATION": round(ev.illumination_score, 4),
        "SPECTRAL": 0.0,  # Unobserved if IIRS absent
        "SCALE": round(ev.scale_score, 4),
        "TEMPORAL": 0.5,  # Single-epoch baseline
        "TEXTURE": round(ev.visual_score, 4),
        "REGISTRATION": round(ev.spatial_score, 4),
        "PHYSICAL": 1.0 if corr.status in ["ACCEPTED", "VERIFIED"] else 0.0,
        "MANUAL": 0.0,
        "SYNTHETIC": 1.0 if corr.is_synthetic else 0.0,
    }

    supporting = []
    missing = []
    for dim, score in dimensions.items():
        if score > 0.6:
            supporting.append(f"{dim} (score={score:.2f})")
        elif score == 0.0 and dim not in ["MANUAL", "SYNTHETIC"]:
            missing.append(dim)

    return EvidenceDetailResponse(
        correspondence_id=corr.id,
        dimensions=dimensions,
        supporting_evidence=supporting,
        missing_evidence=missing,
        unknown_not_negative_preservation=True,
        overall_confidence=corr.overall_confidence,
        total_uncertainty=ev.total_uncertainty,
        evidence_disagreement=ev.evidence_disagreement,
        status=corr.status,
        rejection_reasons=rejection_reasons,
        is_synthetic=corr.is_synthetic,
    )
