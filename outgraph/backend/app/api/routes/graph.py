"""Lunar Entity Knowledge Graph API Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...services.graph_service import GraphService
from ...schemas.graph import ReactFlowGraphResponse

router = APIRouter(prefix="/graph", tags=["Knowledge Graph"])


@router.get("/full", response_model=ReactFlowGraphResponse)
def get_full_graph(db: Session = Depends(get_db)):
    """Retrieves full Lunar Entity Graph serialized for React Flow."""
    graph_service = GraphService(db)
    return graph_service.get_react_flow_graph()


@router.get("/entity/{entity_id}", response_model=ReactFlowGraphResponse)
def get_entity_subgraph(entity_id: str, db: Session = Depends(get_db)):
    """Retrieves subgraph focused around a specific persistent lunar entity."""
    graph_service = GraphService(db)
    return graph_service.get_react_flow_graph(filter_entity_id=entity_id)


@router.get("/observation/{observation_id}", response_model=ReactFlowGraphResponse)
def get_observation_subgraph(observation_id: str, db: Session = Depends(get_db)):
    """Retrieves subgraph focused around a specific observation."""
    graph_service = GraphService(db)
    return graph_service.get_react_flow_graph()
