"""Demo Mission Pipeline API Endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.demo_service import DemoService
from ...schemas.knowledge import DemoMissionResponse

router = APIRouter(prefix="/demo", tags=["Demo Mission"])


@router.post("/run", response_model=DemoMissionResponse)
def run_demo_mission(db: Session = Depends(get_db)):
    """Executes the complete End-to-End Demo Mission."""
    demo_service = DemoService(db)
    result = demo_service.run_complete_demo_mission()
    return DemoMissionResponse(**result)
