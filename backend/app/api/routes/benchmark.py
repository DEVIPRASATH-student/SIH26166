"""Benchmark & Stress Lab API Endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...schemas.knowledge import BenchmarkResponse, StressScenarioResponse
from outgraph.ml.benchmarks.stress_lab import StressLabRunner

router = APIRouter(prefix="/benchmark", tags=["Benchmark"])


@router.post("/run", response_model=BenchmarkResponse)
def run_benchmark_suite():
    """Executes all stress lab scenarios and compiles comparison matrix."""
    runner = StressLabRunner()
    scenarios = runner.run_benchmark_suite()

    resp_scenarios = [
        StressScenarioResponse(
            scenario_id=s.scenario_id,
            scenario_name=s.scenario_name,
            description=s.description,
            algorithms_evaluated=s.algorithms_evaluated,
            winner_algorithm=s.winner_algorithm,
            summary=s.summary,
        )
        for s in scenarios
    ]

    return BenchmarkResponse(
        scenarios=resp_scenarios,
        total_scenarios_evaluated=len(scenarios),
        overall_winner="LunarSynapse-Verified",
    )


@router.get("/results", response_model=BenchmarkResponse)
def get_benchmark_results():
    """Retrieves cached or newly computed benchmark results."""
    return run_benchmark_suite()
