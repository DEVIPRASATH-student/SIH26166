from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.demo_service import DemoService
from ...schemas.knowledge import DemoMissionResponse, DemonstrationScenarioResponse, ScenarioExplanationResponse

router = APIRouter(prefix="/demo", tags=["Demo Mission"])


@router.post("/run", response_model=DemoMissionResponse)
def run_demo_mission(db: Session = Depends(get_db)):
    """Executes the complete End-to-End Demo Mission."""
    demo_service = DemoService(db)
    result = demo_service.run_complete_demo_mission()
    return DemoMissionResponse(**result)


@router.get("/scenarios", response_model=List[DemonstrationScenarioResponse])
def get_demonstration_scenarios(db: Session = Depends(get_db)):
    """Returns the canonical suite of Phase 8.4 demonstration scenarios."""
    demo_service = DemoService(db)
    return demo_service.get_demonstration_scenarios()


@router.get("/scenarios-explanations", response_model=List[ScenarioExplanationResponse])
def get_demonstration_scenario_explanations(db: Session = Depends(get_db)):
    """Returns Phase 8.5 structured explanations for all demonstration scenarios."""
    demo_service = DemoService(db)
    return demo_service.get_demonstration_scenario_explanations()


@router.get("/scenarios/{scenario_id}", response_model=DemonstrationScenarioResponse)
def get_demonstration_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Returns a single demonstration scenario by its identifier."""
    demo_service = DemoService(db)
    scenario = demo_service.get_demonstration_scenario(scenario_id)
    if not scenario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demonstration scenario '{scenario_id}' not found.",
        )
    return scenario


@router.get("/scenarios/{scenario_id}/explanation", response_model=ScenarioExplanationResponse)
def get_demonstration_scenario_explanation(scenario_id: str, db: Session = Depends(get_db)):
    """Returns the Phase 8.5 structured 'Why This Result?' explanation for a scenario."""
    demo_service = DemoService(db)
    explanation = demo_service.get_demonstration_scenario_explanation(scenario_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Explanation for demonstration scenario '{scenario_id}' not found.",
        )
    return explanation


