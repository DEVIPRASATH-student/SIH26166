"""Knowledge Gap, Recommendation, Benchmark, and System Schemas."""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class KnowledgeGapResponse(BaseModel):
    id: str
    entity_id: str
    gap_type: str
    severity: str  # HIGH, MEDIUM, LOW
    reason: str
    recommended_sensor: str
    status: str
    created_at: datetime


class RecommendationRequest(BaseModel):
    entity_id: str
    scientific_question: str = Field("spectral analysis", description="fine morphology, terrain analysis, elevation analysis, spectral analysis")


class RecommendationResponse(BaseModel):
    id: str
    entity_id: str
    scientific_question: str
    recommended_sensor: str
    expected_information_gain: float
    uncertainty_reduction: float
    feasibility: float
    explanation: str
    ranked_sensors: List[Dict[str, Any]]
    created_at: datetime


class StressScenarioResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    description: str
    algorithms_evaluated: List[Dict[str, Any]]
    winner_algorithm: str
    summary: str


class BenchmarkResponse(BaseModel):
    scenarios: List[StressScenarioResponse]
    total_scenarios_evaluated: int
    overall_winner: str


class RedTeamResponse(BaseModel):
    tests: List[Dict[str, Any]]
    total_deceptive_tests: int
    false_positives_prevented: int
    prevention_rate: float


class SystemHealthResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    ml_backends: Dict[str, bool]
    storage_healthy: bool
    total_observations: int
    total_entities: int
    total_verified_matches: int


class DemoMissionResponse(BaseModel):
    status: str
    message: str
    execution_time_seconds: float
    observations_created: int
    correspondences_analyzed: int
    entities_resolved: int
    knowledge_gaps_found: int
    top_recommendation: Dict[str, Any]
