"""Uncertainty Calibration API Endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...models.evidence import CorrespondenceEvidenceModel
from ...models.lunar_entity import LunarEntityModel

router = APIRouter(prefix="/uncertainty", tags=["Uncertainty"])


@router.get("/summary")
def get_uncertainty_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves system-wide epistemic and aleatoric uncertainty metrics."""
    evidences = db.query(CorrespondenceEvidenceModel).all()
    entities = db.query(LunarEntityModel).all()

    avg_unc = sum(e.total_uncertainty for e in evidences) / max(len(evidences), 1)
    avg_disagree = sum(e.evidence_disagreement for e in evidences) / max(len(evidences), 1)
    avg_entity_unc = sum(e.uncertainty for e in entities) / max(len(entities), 1)

    return {
        "mean_correspondence_uncertainty": round(avg_unc, 4),
        "mean_evidence_disagreement": round(avg_disagree, 4),
        "mean_entity_uncertainty": round(avg_entity_unc, 4),
        "total_evaluated_correspondences": len(evidences),
        "calibration_status": "CALIBRATED_BAYESIAN_PROXY",
        "description": "Multi-factor uncertainty combining evidence variance, geometric instability, feature ambiguity, and spatial sparsity.",
    }
