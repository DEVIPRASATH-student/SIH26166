"""Phase 8.5 Explainability, Provenance, and Evidence Visibility Test Suite.
Verifies complete explainability chains, provenance preservation, physical gate integrity,
illumination verification separation, and strict adherence to scientific guardrails.
"""

import os
import subprocess
import pytest
from sqlalchemy.orm import Session

from outgraph.backend.app.database.session import SessionLocal
from outgraph.backend.app.services.demo_service import DemoService
from outgraph.backend.app.schemas.knowledge import ScenarioExplanationResponse


@pytest.fixture(scope="module")
def db_session():
    """Provides a transactional database session for read-only service testing."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="module")
def demo_service(db_session: Session):
    """Provides DemoService instance."""
    return DemoService(db_session)


@pytest.fixture(scope="module")
def explanations(demo_service: DemoService):
    """Provides all Phase 8.5 demonstration scenario explanations."""
    return demo_service.get_demonstration_scenario_explanations()


def test_1_real_negative_control_explanation_exists(demo_service: DemoService):
    """1. Real negative-control explanation exists and reflects non-overlap decision."""
    exp = demo_service.get_demonstration_scenario_explanation("SCENARIO-A")
    assert exp is not None, "Scenario A explanation must exist"
    assert exp["scenario_id"] == "SCENARIO-A"
    assert exp["decision"] == "REJECTED"
    assert "TARGET_OUTSIDE_CALIBRATED_SWATH" in exp["primary_reason"]
    assert exp["judge_card"]["physical_gates_verdict"] == "REJECTED_BY_GATE_3"
    assert "PHYSICAL CORRESPONDENCE NOT VALIDATED" in exp["judge_card"]["high_level_verdict"]


def test_2_synthetic_explanation_marked_synthetic(explanations):
    """2. Synthetic explanations are unambiguously marked as synthetic."""
    for exp in explanations:
        if exp["scenario_id"] != "SCENARIO-A":
            assert exp["provenance"]["is_synthetic"] is True, f"{exp['scenario_id']} must have is_synthetic=True"
            assert "SYNTHETIC" in exp["input_metadata"]["provenance_class"]
            assert "SYNTHETIC" in exp["judge_card"]["is_real_or_synthetic"]
        else:
            assert exp["provenance"]["is_synthetic"] is False, "Scenario A must have is_synthetic=False"
            assert "REAL LUNAR" in exp["input_metadata"]["provenance_class"]


def test_3_provenance_is_preserved(explanations):
    """3. Telemetry and archival provenance is preserved for every scenario."""
    sc_a = next(e for e in explanations if e["scenario_id"] == "SCENARIO-A")
    prov = sc_a["provenance"]
    assert "urn:isro:isda:ch2_cho.ohr" in prov["source_observation"]
    assert "urn:isro:isda:ch2_cho.tmc" in prov["target_observation"]
    assert "OHRC" in prov["sensor_source"]
    assert "TMC-2" in prov["sensor_target"]
    assert prov["source_gsd_m"] == 0.25
    assert prov["target_gsd_m"] == 5.0
    assert "SLDEM2015" in prov["dem_source"]
    assert prov["derived_status"] == "DERIVED RESULT FROM RAW ARCHIVAL OBSERVATIONS"


def test_4_six_gates_correctly_named(explanations):
    """4. The six physical gates must be present and named exactly as established."""
    expected_gate_names = {
        1: "INVALID_SOURCE_GROUNDGRID",
        2: "DEM_OUT_OF_BOUNDS_OR_NODATA",
        3: "TARGET_OUTSIDE_CALIBRATED_SWATH",
        4: "TARGET_CLAMPED_TO_SWATH_BOUNDARY",
        5: "TARGET_OUTSIDE_ELEVATION_CORRIDOR",
        6: "BIDIRECTIONAL_RESIDUAL_TOO_LARGE",
    }
    for exp in explanations:
        gates = exp["physical_gates"]["gates"]
        assert len(gates) == 6, f"Scenario {exp['scenario_id']} must have exactly 6 physical gates"
        for g in gates:
            gid = g["gate_id"]
            assert gid in expected_gate_names, f"Unexpected gate id {gid}"
            assert g["gate_name"] == expected_gate_names[gid], (
                f"Gate {gid} named '{g['gate_name']}', expected '{expected_gate_names[gid]}'"
            )


def test_5_gate_5_is_elevation_corridor(explanations):
    """5. Gate 5 remains strictly TARGET_OUTSIDE_ELEVATION_CORRIDOR."""
    for exp in explanations:
        gate_5 = next(g for g in exp["physical_gates"]["gates"] if g["gate_id"] == 5)
        assert gate_5["gate_name"] == "TARGET_OUTSIDE_ELEVATION_CORRIDOR"
        assert "ELEVATION" in gate_5["gate_name"].upper()
        assert "ILLUMINATION" not in gate_5["gate_name"].upper()


def test_6_illumination_is_not_gate_5(explanations):
    """6. Illumination verification is NOT Gate 5 across all scenarios."""
    for exp in explanations:
        gate_5 = next(g for g in exp["physical_gates"]["gates"] if g["gate_id"] == 5)
        assert "ILLUMINATION" not in gate_5["gate_name"]
        assert "CORRIDOR" in gate_5["gate_name"]
        assert not exp["illumination_evidence"]["section_title"].startswith("GATE 5")
        assert "NOT GATE 5" in exp["illumination_evidence"]["section_title"]



def test_7_illumination_evidence_separately_exposed(explanations):
    """7. Illumination evidence is separately exposed as an independent physics mechanism."""
    for exp in explanations:
        illum = exp["illumination_evidence"]
        assert "ILLUMINATION VERIFICATION" in illum["section_title"]
        assert "status" in illum
        assert "gate_distinction_note" in illum
        assert "NOT Gate 5" in illum["gate_distinction_note"]

    sc_c = next(e for e in explanations if e["scenario_id"] == "SCENARIO-C")
    assert sc_c["illumination_evidence"]["status"] == "REJECTED"
    assert sc_c["illumination_evidence"]["solar_azimuth_difference_deg"] == 180.0
    assert "physically unsupported under the tested conditions" in sc_c["illumination_evidence"]["explanation"]


def test_8_unknown_remains_unknown(explanations):
    """8. Scenario D UNKNOWN state is preserved without forced binary decision."""
    sc_d = next(e for e in explanations if e["scenario_id"] == "SCENARIO-D")
    assert sc_d["decision"] == "UNKNOWN"
    assert "UNKNOWN != NEGATIVE" in sc_d["judge_card"]["high_level_verdict"]
    assert sc_d["geometric_evidence"]["geometric_decision"] == "INSUFFICIENT_EVIDENCE"
    assert sc_d["physical_gates"]["overall_result"] == "NOT_EVALUATED"


def test_9_missing_evidence_not_converted_to_negative(explanations):
    """9. Missing evidence in the 11D ledger is never converted to negative evidence."""
    sc_d = next(e for e in explanations if e["scenario_id"] == "SCENARIO-D")
    ev = sc_d["evidence_dimensions"]
    assert "GEOMETRIC" in ev
    assert ev["GEOMETRIC"]["status"] == "MISSING"
    assert "TERRAIN" in ev
    assert ev["TERRAIN"]["status"] == "UNKNOWN"
    assert "SPECTRAL" in ev
    assert ev["SPECTRAL"]["status"] == "MISSING"
    # Ensure missing statuses are not labeled as REJECTED or CONTRADICTED
    for dim_key in ["SPECTRAL", "GEOMETRIC"]:
        assert ev[dim_key]["status"] in ["MISSING", "UNKNOWN"]


def test_10_entity_association_does_not_imply_correspondence(explanations):
    """10. Spatial proximity / entity association does not imply direct correspondence."""
    sc_a = next(e for e in explanations if e["scenario_id"] == "SCENARIO-A")
    assert sc_a["decision"] == "REJECTED"
    assert "Boguslawsky" in sc_a["judge_card"]["does_this_mean_images_are_unrelated"]
    assert "physical ground overlap does not exist" in sc_a["judge_card"]["does_this_mean_images_are_unrelated"]


def test_11_uncertainty_explanation_preserves_unknown(explanations):
    """11. Uncertainty quantification preserves UNKNOWN state and calibration status."""
    sc_a = next(e for e in explanations if e["scenario_id"] == "SCENARIO-A")
    assert sc_a["uncertainty"]["status"] == "UNKNOWN"
    assert (
        "REAL-LUNAR EMPIRICAL UNCERTAINTY CALIBRATION NOT ESTABLISHED"
        in sc_a["uncertainty"]["calibration_statement"]
    )
    assert sc_a["uncertainty"]["scalar_uncertainty"] == 0.95
    assert sc_a["uncertainty"]["decomposition"]["spatial_sparsity"] is not None


def test_12_saturation_limitation_remains_visible(explanations):
    """12. Feature-dispersion uncertainty saturation above 4 px limit remains documented."""
    for exp in explanations:
        assert (
            "4 px" in exp["uncertainty"]["saturation_note"]
            or "4.0 px" in exp["uncertainty"]["saturation_note"]
        )
    sc_a = next(e for e in explanations if e["scenario_id"] == "SCENARIO-A")
    assert any("4 px" in lim for lim in sc_a["limitations"])


def test_13_nbo_uses_potentially_reduces_uncertainty(explanations):
    """13. All recommendations use POTENTIALLY_REDUCES_UNCERTAINTY exclusively."""
    for exp in explanations:
        if exp["recommendation"]:
            rec = exp["recommendation"]
            assert rec["recommendation_type"] == "POTENTIALLY_REDUCES_UNCERTAINTY"
            assert "POTENTIALLY_REDUCES_UNCERTAINTY" in rec["recommendation_type"]
            assert "No spacecraft tasking or orbital mechanics are simulated" in rec["disclaimer"]


def test_14_no_will_resolve_in_explanations(explanations):
    """14. Forbidden phrasing 'WILL_RESOLVE' is never used."""
    import json
    raw_str = json.dumps(explanations)
    assert "WILL_RESOLVE" not in raw_str
    assert "will_resolve" not in raw_str.lower()
    assert "will resolve" not in raw_str.lower()


def test_15_no_forbidden_claims_in_explanations(explanations):
    """15. Scientific guardrail: no forbidden absolute claims."""
    import json
    raw_str = json.dumps(explanations).lower()
    forbidden_terms = [
        "100% accurate",
        "guaranteed",
        "confirmed lunar match",
        "ai proved",
        "universally invariant",
        "real-time spacecraft tasking",
        "validated real-lunar accuracy",
        "calibrated real-lunar uncertainty",
        "wrong lunar feature",
        "never fails",
        "eliminates false positives",
    ]
    for term in forbidden_terms:
        assert term not in raw_str, f"Forbidden term '{term}' found in scenario explanations"


def test_16_real_benchmark_values_remain_unchanged(explanations):
    """16. Historical Phase 7 benchmark values (31 candidates, 8 inliers, 25.81%) are preserved."""
    sc_a = next(e for e in explanations if e["scenario_id"] == "SCENARIO-A")
    hist = sc_a["candidate_generation"]["historical_phase7_benchmark"]
    assert hist["candidate_count"] == 31
    assert hist["geometric_inliers"] == 8
    assert hist["inlier_ratio_pct"] == 25.81


def test_17_current_demonstration_instance_distinguishable(explanations):
    """17. Current demonstration instance (26 candidates) is distinguishable from benchmark."""
    sc_a = next(e for e in explanations if e["scenario_id"] == "SCENARIO-A")
    curr = sc_a["candidate_generation"]["current_demonstration_instance"]
    assert curr["candidate_count"] == 26
    assert curr["candidate_count"] != sc_a["candidate_generation"]["historical_phase7_benchmark"]["candidate_count"]


def test_18_raw_data_remains_unchanged():
    """18. Raw data directory data/real/ remains completely untouched."""
    # Verify via git diff/status
    res = subprocess.run(
        ["git", "diff", "--stat", "data/real/"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert res.stdout.strip() == "", "data/real/ has modified tracked content"


def test_pydantic_schema_validation(explanations):
    """Validates that all scenario explanation dictionaries satisfy ScenarioExplanationResponse."""
    for exp in explanations:
        validated = ScenarioExplanationResponse(**exp)
        assert validated.scenario_id == exp["scenario_id"]
        assert len(validated.physical_gates["gates"]) == 6
        assert len(validated.explainability_trace) >= 5
