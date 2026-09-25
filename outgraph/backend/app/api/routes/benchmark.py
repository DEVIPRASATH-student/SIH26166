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


@router.get("/phase2")
def get_phase2_benchmark_results(pair_id: str = None, matcher: str = None):
    """Retrieves Phase 2 Real-Data Correspondence Baseline benchmark results."""
    from outgraph.ml.benchmark.phase2_runner import Phase2BenchmarkRunner
    import os, json

    output_dir = "results/phase2"
    json_path = os.path.join(output_dir, "benchmark_results.json")
    summary_path = os.path.join(output_dir, "benchmark_summary.json")

    # Run runner if cached results do not exist yet
    if not os.path.exists(json_path):
        runner = Phase2BenchmarkRunner(output_dir=output_dir)
        matchers = [matcher] if matcher else ["SIFT", "ORB", "SUPERPOINT", "LOFTR", "RIFT"]
        results = runner.run_benchmark(pair_id=pair_id, matcher_names=matchers, include_synthetic=True)
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            results = json.load(f)

    if pair_id:
        results = [r for r in results if r.get("pair_id") == pair_id]
    if matcher:
        results = [r for r in results if r.get("matcher") == matcher]

    summary = {}
    if os.path.exists(summary_path):
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

    return {
        "phase": "Phase 2 — Real-Data Correspondence Baseline",
        "total_results": len(results),
        "summary": summary,
        "results": results,
    }

