"""React Flow Graph Schemas."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ReactFlowNode(BaseModel):
    id: str
    type: str  # "entityNode", "observationNode", "sensorNode", "evidenceNode", "hypothesisNode"
    position: Dict[str, float]  # {"x": 100.0, "y": 200.0}
    data: Dict[str, Any]


class ReactFlowEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None  # "OBSERVED_BY", "SUPPORTS", "DERIVED_FROM", etc.
    animated: bool = False
    style: Optional[Dict[str, Any]] = None


class ReactFlowGraphResponse(BaseModel):
    nodes: List[ReactFlowNode]
    edges: List[ReactFlowEdge]
    total_entities: int
    total_observations: int
    total_evidence_nodes: int
