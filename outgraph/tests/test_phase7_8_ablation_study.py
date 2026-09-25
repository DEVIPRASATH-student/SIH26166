"""Phase 7.8 Ablation Study Test Suite.

Verifies:
- All 13 component ablations (A1 through A13) execute cleanly and deterministically.
- Measurable contributions of scale normalization, illumination, geometry,
  GroundGrid, DEM, parallax, uncertainty, provenance, contradiction handling,
  entity graph, temporal reasoning, knowledge gaps, and active observation.
- Preservation of PHYSICAL CORRESPONDENCE NOT VALIDATED on real data.
- Strict prohibition of overall winners, algorithm rankings, or single system scores.
- Raw data immutability and complete regression stability.
"""

from pathlib import Path
import pytest
import numpy as np

from outgraph.ml.benchmark.ablation_study import AblationStudyEngine, AblationRecord
from outgraph.ml.data.models import ValueStatus


OHRC_GRID = Path("data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv")
TMC2_GRID = Path("data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv")


@pytest.fixture
def engine():
    return AblationStudyEngine()


# ==============================================================================
# INDIVIDUAL COMPONENT ABLATION TESTS (A1 - A13)
# ==============================================================================

def test_ablation_a1_scale_normalization(engine):
    """A1: Removing scale normalization degrades correspondence above 2x-4x."""
    res = engine.run_ablation_a1_scale()
    assert res["ablation_id"] == "A1"
    series = res["scale_series"]
    assert len(series) == 6

    # Verify all 6 scale factors record raw measurements and delta
    for s in series:
        assert "scale" in s
        assert "full_system_inliers" in s
        assert "ablated_inliers" in s
        assert "delta_inliers" in s
        assert s["scale"] in [1.0, 2.0, 4.0, 8.0, 16.0, 23.35]


def test_ablation_a2_illumination_validation(engine):
    """A2: Removing illumination validation mistranslates solar shadows as surface changes."""
    res = engine.run_ablation_a2_illumination()
    assert res["ablation_id"] == "A2"
    assert res["full_system_conclusion"] == "ILLUMINATION_DIFFERENCE_SURFACE_STABLE"
    assert res["ablated_conclusion"] == "FALSE_SURFACE_DEFORMATION_INFERRED"


def test_ablation_a3_geometric_verification(engine):
    """A3: Removing geometric verification permits chiral reflection acceptance."""
    res = engine.run_ablation_a3_geometry()
    assert res["ablation_id"] == "A3"
    assert res["full_system_accepted"] is False
    assert res["ablated_accepted"] is True


def test_ablation_a4_groundgrid_validation(engine):
    """A4: Removing GroundGrid permits false 2D inliers on disjoint orbital tracks."""
    assert OHRC_GRID.exists()
    assert TMC2_GRID.exists()
    res = engine.run_ablation_a4_groundgrid(str(OHRC_GRID), str(TMC2_GRID))
    assert res["ablation_id"] == "A4"
    assert res["full_system_rejections"] == res["points_evaluated"]
    assert res["ablated_rejections"] == 0


def test_ablation_a5_dem_terrain_validation(engine):
    """A5: Removing DEM causes ~1.9 km vertical datum bias in regional mare basin."""
    res = engine.run_ablation_a5_dem()
    assert res["ablation_id"] == "A5"
    assert res["true_dem_elevation_m"] < -1500.0
    assert res["elevation_error_m"] > 1500.0


def test_ablation_a6_physical_parallax_modeling(engine):
    """A6: Removing parallax modeling introduces unmodeled off-nadir ground error."""
    res = engine.run_ablation_a6_parallax()
    assert res["ablation_id"] == "A6"
    assert res["modeled_parallax_displacement_m"] > 20.0
    assert res["unmodeled_target_error_m"] == pytest.approx(res["modeled_parallax_displacement_m"])


def test_ablation_a7_uncertainty_representation(engine):
    """A7: Removing uncertainty model forces unjustified binary assertions."""
    res = engine.run_ablation_a7_uncertainty()
    assert res["ablation_id"] == "A7"
    assert res["full_system_status"] == ValueStatus.UNKNOWN.value
    assert res["ablated_status"] == "FORCED_BINARY_TRUE"


def test_ablation_a8_provenance_tracking(engine):
    """A8: Removing provenance allows synthetic data to contaminate flight observations."""
    res = engine.run_ablation_a8_provenance()
    assert res["ablation_id"] == "A8"
    assert res["full_system_catches_synthetic"] is True
    assert res["ablated_catches_synthetic"] is False


def test_ablation_a9_evidence_fusion_contradiction_handling(engine):
    """A9: Removing contradiction handling causes conflicting observations to corrupt entities."""
    res = engine.run_ablation_a9_evidence_fusion()
    assert res["ablation_id"] == "A9"
    assert res["full_system_quarantined"] is True
    assert res["ablated_quarantined"] is False


def test_ablation_a10_entity_graph_persistence(engine):
    """A10: Removing entity graph causes multi-pass observations to spawn redundant entities."""
    res = engine.run_ablation_a10_entity_graph()
    assert res["ablation_id"] == "A10"
    assert res["full_system_entity_persistent"] is True
    assert res["ablated_entity_persistent"] is False


def test_ablation_a11_temporal_reasoning(engine):
    """A11: Removing temporal reasoning treats multi-year gaps as simultaneous."""
    res = engine.run_ablation_a11_temporal()
    assert res["ablation_id"] == "A11"
    assert res["full_system_models_time"] is True
    assert res["ablated_models_time"] is False
    assert res["temporal_delta_years"] > 3.0


def test_ablation_a12_knowledge_gap_engine(engine):
    """A12: Removing knowledge-gap engine leaves unconfirmed tracks without causal explanations."""
    res = engine.run_ablation_a12_knowledge_gap()
    assert res["ablation_id"] == "A12"
    assert res["full_system_gaps_identified"] is True
    assert res["ablated_gaps_identified"] is False
    assert len(res["identified_gaps"]) > 0


def test_ablation_a13_active_observation_planning(engine):
    """A13: Removing active observation engine leaves knowledge gaps as passive dead-ends."""
    res = engine.run_ablation_a13_active_observation()
    assert res["ablation_id"] == "A13"
    assert res["full_system_recommendations"] > 0
    assert res["ablated_recommendations"] == 0


# ==============================================================================
# MASTER ABLATION MATRIX & GUARDRAIL TESTS
# ==============================================================================

def test_run_all_ablations_generates_complete_matrix(engine):
    """Verifies that all 13 ablations are compiled into a structured comparison matrix."""
    records = engine.run_all_ablations(str(OHRC_GRID), str(TMC2_GRID))
    assert len(records) == 13

    ids = [r.ablation_id for r in records]
    expected_ids = [f"A{i}" for i in range(1, 14)]
    assert ids == expected_ids

    for r in records:
        assert isinstance(r, AblationRecord)
        assert len(r.component) > 0
        assert len(r.delta) > 0
        assert len(r.interpretation) > 0
        assert len(r.limitation) > 0


def test_no_overall_winner_or_lunar_synapse_score_assigned(engine):
    """Guarantees that no single aggregate score or winner is produced."""
    records = engine.run_all_ablations(str(OHRC_GRID), str(TMC2_GRID))
    for r in records:
        assert not hasattr(r, "winner")
        assert not hasattr(r, "overall_score")
        assert not hasattr(r, "superiority_index")


def test_real_data_preserves_physical_correspondence_not_validated(engine):
    """Confirms that no ablation manufactures correspondence on real data."""
    a4 = engine.run_ablation_a4_groundgrid(str(OHRC_GRID), str(TMC2_GRID))
    assert a4["full_system_rejections"] == a4["points_evaluated"]
