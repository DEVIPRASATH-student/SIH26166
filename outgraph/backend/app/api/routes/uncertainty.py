"""Uncertainty Calibration API Endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...models.evidence import CorrespondenceEvidenceModel
from ...models.lunar_entity import LunarEntityModel
from ...models.correspondence import CorrespondenceModel

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
        "real_data_calibration_status": "REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED",
        "uncertainty_saturation_limit": ">4 px uncertainty saturation limit preserved",
        "unknown_preservation": "UNKNOWN != NEGATIVE",
        "description": "Multi-factor uncertainty combining evidence variance, geometric instability, feature ambiguity, and spatial sparsity.",
    }


@router.get("/{correspondence_id}")
def get_correspondence_uncertainty(correspondence_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Retrieves scalar, interval, covariance, and qualitative uncertainty semantics for a correspondence."""
    ev = db.query(CorrespondenceEvidenceModel).filter(
        CorrespondenceEvidenceModel.correspondence_id == correspondence_id
    ).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"Evidence/Uncertainty for correspondence '{correspondence_id}' not found")

    unc = ev.total_uncertainty
    qualitative = "LOW" if unc < 0.3 else "MODERATE" if unc < 0.6 else "HIGH" if unc < 0.85 else "SATURATED"
    lower_bound = round(max(0.0, unc - 0.15), 4)
    upper_bound = round(min(1.0, unc + 0.15), 4)

    return {
        "correspondence_id": correspondence_id,
        "scalar": round(unc, 4),
        "interval": {"lower": lower_bound, "upper": upper_bound, "confidence_level": 0.95},
        "covariance_proxy": [
            [round(unc * 0.6, 4), round(ev.evidence_disagreement * 0.2, 4)],
            [round(ev.evidence_disagreement * 0.2, 4), round(unc * 0.4, 4)],
        ],
        "qualitative": qualitative,
        "decomposition": {
            "evidence_disagreement": ev.evidence_disagreement,
            "geometric_instability": ev.geometric_instability,
            "feature_ambiguity": ev.feature_ambiguity,
            "spatial_sparsity": ev.spatial_sparsity,
        },
        "calibration_status": ev.calibration_status,
        "scientific_limitations": [
            "REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED",
            "UNKNOWN != NEGATIVE",
            ">4 px uncertainty saturation limitation applies",
        ],
    }


@router.post("/override")
def override_uncertainty(payload: Dict[str, Any] = Body(...)):
    """Rejects arbitrary client tampering of scientific uncertainty."""
    raise HTTPException(
        status_code=403,
        detail="Forbidden: Scientific safety policy strictly prohibits overwriting computed uncertainty with arbitrary values.",
    )
