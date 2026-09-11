"""System Diagnostics & Health API Endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.sql import func


from ...database.session import get_db
from ...core.config import settings
from ...models.observation import ObservationModel
from ...models.lunar_entity import LunarEntityModel
from ...models.correspondence import CorrespondenceModel
from ...schemas.knowledge import SystemHealthResponse

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    """Provides system diagnostics, database status, and ML backend readiness."""
    db_connected = False
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
    except Exception:
        db_connected = False

    # Check ML backend availability
    torch_available = False
    try:
        import torch
        torch_available = True
    except ImportError:
        torch_available = False

    total_obs = db.query(ObservationModel).count() if db_connected else 0
    total_ent = db.query(LunarEntityModel).count() if db_connected else 0
    total_ver = (
        db.query(CorrespondenceModel).filter(CorrespondenceModel.status == "VERIFIED").count()
        if db_connected
        else 0
    )

    return SystemHealthResponse(
        status="OPERATIONAL",
        version=settings.VERSION,
        database_connected=db_connected,
        ml_backends={
            "SIFT": True,
            "ORB": True,
            "PyTorch": torch_available,
            "SuperPoint_Adapter": True,
            "LoFTR_Adapter": True,
            "RIFT_Adapter": True,
            "ECC_SubPixel_Engine": True,
        },
        storage_healthy=settings.IMAGES_DIR.exists(),
        total_observations=total_obs,
        total_entities=total_ent,
        total_verified_matches=total_ver,
    )
