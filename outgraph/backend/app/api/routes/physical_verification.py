"""Physical Verification API Endpoints."""

import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.correspondence_service import CorrespondenceService
from ...schemas.physical_verification import PhysicalGateResult, PhysicalVerificationResponse

router = APIRouter(prefix="/physical-verification", tags=["Physical Verification"])

GATE_CATALOG = {
    "GATE1": {
        "gate_id": "GATE1",
        "gate_name": "INVALID_SOURCE_GROUNDGRID",
        "description": "Verifies that source observation has a calibrated flight pushbroom SPICE GroundGrid.",
        "failure_criterion": "GroundGrid is missing, uncalibrated, or contains degenerate coordinates.",
        "threshold": "GroundGrid coordinates non-empty and non-singular",
    },
    "GATE2": {
        "gate_id": "GATE2",
        "gate_name": "DEM_OUT_OF_BOUNDS_OR_NODATA",
        "description": "Verifies that target ray intersection falls within SLDEM2015 topographic bounds with valid elevation.",
        "failure_criterion": "Intersection outside lunar DEM tiles or NODATA returned.",
        "threshold": "Elevation valid in SLDEM2015 range [-9000m, +11000m]",
    },
    "GATE3": {
        "gate_id": "GATE3",
        "gate_name": "TARGET_OUTSIDE_CALIBRATED_SWATH",
        "description": "Verifies that target keypoints lie within the calibrated physical footprint swath of the target sensor.",
        "failure_criterion": "Sensor footprints are physically separated or keypoint is outside sensor swath boundary.",
        "threshold": "Spatial overlap > 0.0% across calibrated GroundGrid polygons",
    },
    "GATE4": {
        "gate_id": "GATE4",
        "gate_name": "TARGET_CLAMPED_TO_SWATH_BOUNDARY",
        "description": "Detects if projection was artificially clamped to the boundary edge of the sensor swath.",
        "failure_criterion": "Target coordinate falls exactly on swath boundary pixel edge.",
        "threshold": "Distance from swath boundary > 0 px",
    },
    "GATE5": {
        "gate_id": "GATE5",
        "gate_name": "TARGET_OUTSIDE_ELEVATION_CORRIDOR",
        "description": "Checks if elevation profile along the parallax ray corridor exceeds local topographic envelope.",
        "failure_criterion": "Corridor elevation bounds exceed min/max terrain height profile.",
        "threshold": "Elevation corridor width within DEM envelope",
    },
    "GATE6": {
        "gate_id": "GATE6",
        "gate_name": "BIDIRECTIONAL_RESIDUAL_TOO_LARGE",
        "description": "Verifies forward-backward pushbroom ray-casting consistency residual.",
        "failure_criterion": "Residual distance between forward projection and reverse ray-cast exceeds threshold.",
        "threshold": "Residual <= 4.0 px",
    },
}


@router.get("/gates")
def get_gate_definitions() -> Dict[str, Any]:
    """Returns the catalog, definitions, and thresholds for all six physical gates."""
    return {
        "description": "Six-Gate Physics Verification Engine (Phase 3)",
        "gates": GATE_CATALOG,
        "policy": "Physical verification cannot be bypassed. Rejection is preserved without forced matching.",
    }


@router.get("/{correspondence_id}", response_model=PhysicalVerificationResponse)
def get_physical_verification_result(correspondence_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed Six-Gate physical verification evaluation for a correspondence."""
    corr_service = CorrespondenceService(db)
    corr = corr_service.get_correspondence(correspondence_id)
    if not corr:
        raise HTTPException(status_code=404, detail=f"Correspondence '{correspondence_id}' not found")

    ev = corr_service.get_evidence(corr.id)
    rejection_reasons = []
    if ev and ev.rejection_reasons_json:
        rejection_reasons = json.loads(ev.rejection_reasons_json)

    reasons_str = " ".join(rejection_reasons)
    phys_passed = (corr.status not in ["REJECTED", "GEOMETRICALLY_DEGENERATE"]) and (corr.num_inliers > 0)
    is_synth = bool(corr.is_synthetic)

    gates_evaluated = {}
    for gid, ginfo in GATE_CATALOG.items():
        failed = f"{gid}_{ginfo['gate_name']}" in reasons_str
        status_val = "REJECTED" if failed else ("PASS" if phys_passed else "NOT_EVALUATED")
        reason_val = f"Failed: {ginfo['failure_criterion']}" if failed else f"Passed physical check ({ginfo['threshold']})"
        gates_evaluated[gid] = PhysicalGateResult(
            gate_id=gid,
            gate_name=ginfo["gate_name"],
            status=status_val,
            reason=reason_val,
            threshold=ginfo["threshold"],
            observed_value="FAIL" if failed else "PASS",
        )

    limitations = [
        "PHYSICAL CORRESPONDENCE NOT VALIDATED" if not is_synth else "SYNTHETIC CONTROLLED SCENARIO ONLY",
        "REAL-DATA ACCURACY = N/A",
        "REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED",
    ]

    return PhysicalVerificationResponse(
        correspondence_id=corr.id,
        passed=phys_passed,
        status="PASS" if phys_passed else "REJECTED",
        gates=gates_evaluated,
        rejection_reasons=rejection_reasons,
        limitations=limitations,
        provenance={"is_synthetic": is_synth, "type": "SYNTHETIC" if is_synth else "REAL_LUNAR"},
    )
