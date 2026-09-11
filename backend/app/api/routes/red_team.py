"""Adversarial Red Team API Endpoints."""

from fastapi import APIRouter
from ...schemas.knowledge import RedTeamResponse
from outgraph.ml.benchmarks.red_team import RedTeamRunner

router = APIRouter(prefix="/red-team", tags=["Red Team"])


@router.post("/run", response_model=RedTeamResponse)
def run_red_team_tests():
    """Runs deceptive adversarial correspondence challenges."""
    runner = RedTeamRunner()
    results = runner.run_all_adversarial_tests()

    tests_list = []
    prevented_count = 0

    for r in results:
        if r.final_decision == "CORRECTLY_REJECTED":
            prevented_count += 1
        tests_list.append({
            "test_id": r.test_id,
            "name": r.name,
            "attack_vector": r.attack_vector,
            "raw_matcher_result": r.raw_matcher_result,
            "physics_verification_result": r.physics_verification_result,
            "final_decision": r.final_decision,
            "rejection_reasons": r.rejection_reasons,
            "evidence_breakdown": r.evidence_breakdown,
            "explanation": r.explanation,
        })

    rate = float(prevented_count / max(len(results), 1))

    return RedTeamResponse(
        tests=tests_list,
        total_deceptive_tests=len(results),
        false_positives_prevented=prevented_count,
        prevention_rate=round(rate, 2),
    )
