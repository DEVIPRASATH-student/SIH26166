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
    is_synthetic: bool = True
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
    uncertainty_reduction_basis: str = Field("POTENTIALLY_REDUCES_UNCERTAINTY", description="Strict epistemic reduction basis")
    feasibility: float
    payload_status: str = Field("AVAILABLE", description="AVAILABLE or PAYLOAD_UNAVAILABLE")
    explanation: str
    sensor_requirement: Optional[str] = None
    spatial_requirement: Optional[str] = None
    temporal_requirement: Optional[str] = None
    rationale: Optional[str] = None
    ranked_sensors: List[Dict[str, Any]] = Field(default_factory=list)
    provenance: Optional[Dict[str, Any]] = None
    data_provenance: Optional[Dict[str, Any]] = None
    is_synthetic: bool = True
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


class SystemStatusResponse(BaseModel):
    status: str
    version: str
    database_connected: bool
    scientific_pipeline: str
    dem_availability: Dict[str, Any]
    groundgrid_availability: Dict[str, Any]
    ml_backends: Dict[str, bool]
    raw_data_integrity: str
    storage_healthy: bool
    total_observations: int
    total_entities: int
    total_verified_matches: int
    subsystems: Optional[Dict[str, str]] = None


class DemoMissionResponse(BaseModel):

    status: str
    message: str
    execution_time_seconds: float
    observations_created: int
    correspondences_analyzed: int
    entities_resolved: int
    knowledge_gaps_found: int
    top_recommendation: Dict[str, Any]


class DemonstrationScenarioResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    scenario_type: str
    real_or_synthetic: str
    is_synthetic: bool
    source_observation: str
    target_observation: str
    correspondence_id: Optional[str] = None
    candidate_count: int
    candidate_count_notes: Optional[str] = None
    geometric_result: str
    physical_result: str
    gate_metrics_notes: Optional[str] = None
    evidence_state: Dict[str, Any]
    uncertainty_state: Dict[str, Any]
    knowledge_gap: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None
    limitations: List[str]


class ScenarioExplanationResponse(BaseModel):
    scenario_id: str
    scenario_name: str
    decision: str
    primary_reason: str
    summary: str
    judge_card: Dict[str, Any]
    provenance: Dict[str, Any]
    input_metadata: Dict[str, Any]
    candidate_generation: Dict[str, Any]
    geometric_evidence: Dict[str, Any]
    physical_gates: Dict[str, Any]
    illumination_evidence: Dict[str, Any]
    evidence_dimensions: Dict[str, Any]
    uncertainty: Dict[str, Any]
    knowledge_gap: Optional[Dict[str, Any]] = None
    recommendation: Optional[Dict[str, Any]] = None
    explainability_trace: List[Dict[str, Any]]
    limitations: List[str]


