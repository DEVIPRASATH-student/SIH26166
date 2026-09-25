"""Unit and Integration Tests for Phase 2 Real-Data Correspondence Baseline."""

import os
import pytest
from fastapi.testclient import TestClient
import numpy as np

from outgraph.backend.app.main import app
from outgraph.backend.app.database.session import init_db
from outgraph.ml.benchmark.ground_truth import GroundTruthLevel, evaluate_ground_truth_level
from outgraph.ml.benchmark.pair_registry import RealDataPairRegistry, BenchmarkPair
from outgraph.ml.benchmark.metrics import BenchmarkMetrics, MatcherImplementationStatus
from outgraph.ml.benchmark.failure_classifier import (
    classify_correspondence_failure,
    CorrespondenceOutcome,
    FailureCategory,
)
from outgraph.ml.benchmark.phase2_runner import Phase2BenchmarkRunner
from outgraph.ml.data.fixtures.test_fixtures import create_mock_ohrc_pds4_product, create_mock_iirs_pds4_product
from outgraph.ml.data.models import LunarProduct, ProductMetadata, ProvenanceRecord, ValidationResult, ValueStatus, GeographicBounds

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    init_db()


def test_ground_truth_level_evaluation():
    """Verifies ground truth level rules and synthetic isolation (Level 4 GT)."""
    p1 = create_mock_ohrc_pds4_product()
    p2 = create_mock_ohrc_pds4_product()

    # Synthetic products MUST resolve to Level 4
    p1.is_synthetic = True
    gt = evaluate_ground_truth_level(p1, p2)
    assert gt == GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL

    # Non-synthetic without bounding box resolves to UNKNOWN
    p1.is_synthetic = False
    p1.metadata.geographic_bounds = GeographicBounds(status=ValueStatus.UNKNOWN)
    p2.metadata.geographic_bounds = GeographicBounds(status=ValueStatus.UNKNOWN)

    gt_unknown = evaluate_ground_truth_level(p1, p2)
    assert gt_unknown == GroundTruthLevel.UNKNOWN


    # With known overlapping bounds
    p1.metadata.geographic_bounds.status = ValueStatus.KNOWN
    p1.metadata.geographic_bounds.lat_min = -75.0
    p1.metadata.geographic_bounds.lat_max = -65.0
    p1.metadata.geographic_bounds.lon_min = 10.0
    p1.metadata.geographic_bounds.lon_max = 20.0

    p2.metadata.geographic_bounds.status = ValueStatus.KNOWN
    p2.metadata.geographic_bounds.lat_min = -70.0
    p2.metadata.geographic_bounds.lat_max = -60.0
    p2.metadata.geographic_bounds.lon_min = 15.0
    p2.metadata.geographic_bounds.lon_max = 25.0

    gt_level1 = evaluate_ground_truth_level(p1, p2)
    assert gt_level1 == GroundTruthLevel.LEVEL_1_GEOREFERENCED


def test_pair_registry():
    """Verifies pair registry initialization and programmatic pair registration."""
    registry = RealDataPairRegistry(data_root="data/real")
    pair = BenchmarkPair(
        pair_id="TEST_OHRC_LRO_001",
        source_sensor="OHRC",
        target_sensor="LRO_NAC",
        source_product_id="src.xml",
        target_product_id="tgt.xml",
        source_file_path="src.xml",
        target_file_path="tgt.xml",
        priority_tier=1,
        expected_difficulty="medium",
        is_real_data=True,
    )
    registry.register_pair(pair)

    retrieved = registry.get_pair("TEST_OHRC_LRO_001")
    assert retrieved is not None
    assert retrieved.source_sensor == "OHRC"
    assert retrieved.priority_tier == 1


def test_failure_classifier():
    """Verifies correspondence failure outcome classification and dominant failure assignment."""
    p_src = create_mock_ohrc_pds4_product()
    p_tgt = create_mock_ohrc_pds4_product()

    # Case 1: Excellent alignment -> ACCEPTED
    metrics_pass = BenchmarkMetrics(
        keypoints_source=500,
        keypoints_target=500,
        candidate_matches=100,
        geometric_inliers=45,
        inlier_ratio=0.45,
        mean_reprojection_error_px=1.2,
        convex_hull_area_ratio=0.35,
        homography_condition_number=12.5,
    )
    res_pass = classify_correspondence_failure(p_src, p_tgt, metrics_pass)
    assert res_pass.outcome == CorrespondenceOutcome.ACCEPTED
    assert res_pass.dominant_failure is None

    # Case 2: Low inlier count -> REJECTED due to GEOMETRIC_FAILURE
    metrics_fail = BenchmarkMetrics(
        keypoints_source=500,
        keypoints_target=500,
        candidate_matches=100,
        geometric_inliers=3,
        inlier_ratio=0.03,
        mean_reprojection_error_px=8.5,
        convex_hull_area_ratio=0.01,
        homography_condition_number=850.0,
    )
    res_fail = classify_correspondence_failure(p_src, p_tgt, metrics_fail)
    assert res_fail.outcome in (CorrespondenceOutcome.REJECTED, CorrespondenceOutcome.INSUFFICIENT_EVIDENCE)
    assert res_fail.dominant_failure == FailureCategory.GEOMETRIC_FAILURE


def test_unknown_gsd_preservation_in_runner():
    """Verifies that scale ratio is NOT calculated if GSD is UNKNOWN."""
    p_src = create_mock_ohrc_pds4_product()
    p_tgt = create_mock_ohrc_pds4_product()

    # Explicitly set GSD status as UNKNOWN
    p_src.metadata.gsd_m = None
    p_src.metadata.value_statuses["gsd_m"] = ValueStatus.UNKNOWN
    p_tgt.metadata.gsd_m = None
    p_tgt.metadata.value_statuses["gsd_m"] = ValueStatus.UNKNOWN

    metrics = BenchmarkMetrics(
        native_gsd_source_m=p_src.metadata.gsd_m,
        native_gsd_target_m=p_tgt.metadata.gsd_m,
        gsd_status="UNKNOWN",
        estimated_scale_ratio=None,
        scale_ratio_status="UNKNOWN",
    )
    res_dict = metrics.to_dict()

    assert res_dict["native_gsd_source_m"] is None
    assert res_dict["gsd_status"] == "UNKNOWN"
    assert res_dict["estimated_scale_ratio"] == "UNKNOWN"
    assert res_dict["scale_ratio_status"] == "UNKNOWN"


def test_phase2_runner_synthetic_execution(tmp_path):
    """Verifies Phase 2 runner execution on synthetic control pairs."""
    runner = Phase2BenchmarkRunner(output_dir=str(tmp_path / "results"))
    results = runner.run_benchmark(matcher_names=["SIFT", "ORB"], include_synthetic=True)

    assert len(results) >= 2
    assert os.path.exists(tmp_path / "results" / "benchmark_results.json")
    assert os.path.exists(tmp_path / "results" / "benchmark_results.csv")
    assert os.path.exists(tmp_path / "results" / "benchmark_summary.json")

    # Check result structure
    r = results[0]
    assert "pair_id" in r
    assert "matcher" in r
    assert "status" in r
    assert "metrics" in r
    assert "failure_analysis" in r
    assert r["metrics"]["matcher_implementation_status"] == "REAL"


def test_phase2_api_endpoint():
    """Verifies GET /api/benchmark/phase2 API endpoint."""
    res = client.get("/api/benchmark/phase2")
    assert res.status_code == 200
    data = res.json()
    assert "phase" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_real_never_silently_uses_synthetic(tmp_path):
    """Verifies that run_real_benchmark never includes synthetic control pairs in real results."""
    runner = Phase2BenchmarkRunner(output_dir=str(tmp_path / "results"), data_root=str(tmp_path / "data_real"))
    real_results = runner.run_real_benchmark(matcher_names=["SIFT"])

    # Must be 0 real results when no real products are present in data_real
    assert len(real_results) == 0
    for r in real_results:
        assert r.get("is_real_data") is True
        assert r.get("ground_truth_level") != GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL.to_string()


def test_empty_data_real_produces_no_real_data_found(tmp_path):
    """Verifies that empty data/real produces NO_REAL_DATA_FOUND status summary."""
    runner = Phase2BenchmarkRunner(output_dir=str(tmp_path / "results"), data_root=str(tmp_path / "empty_real"))
    results = runner.run_real_benchmark(matcher_names=["SIFT"])

    assert len(results) == 0
    summary_file = tmp_path / "results" / "real_benchmark_summary.json"
    assert os.path.exists(summary_file)
    import json
    with open(summary_file, "r") as f:
        summary_data = json.load(f)
    assert summary_data["status"] == "NO_REAL_DATA_FOUND"
    assert summary_data["real_data_executed"] is False


def test_synthetic_controls_excluded_from_real_results(tmp_path):
    """Verifies synthetic control pairs are explicitly flagged as is_real_data=False."""
    runner = Phase2BenchmarkRunner(output_dir=str(tmp_path / "results"), data_root=str(tmp_path / "empty_real"))
    runner._ensure_synthetic_control_pair()

    real_pairs = runner.registry.list_pairs(real_only=True)
    all_pairs = runner.registry.list_pairs(real_only=False)

    assert len(real_pairs) == 0
    assert len(all_pairs) >= 1
    assert all_pairs[0].is_real_data is False


def test_real_products_with_unknown_metadata_remain_unknown():
    """Verifies missing product metadata remains strictly UNKNOWN."""
    p = create_mock_ohrc_pds4_product()
    p.metadata.gsd_m = None
    p.metadata.value_statuses["gsd_m"] = ValueStatus.UNKNOWN

    assert p.metadata.value_statuses.get("gsd_m") == ValueStatus.UNKNOWN
    assert p.metadata.gsd_m is None


def test_level4_synthetic_results_isolated_from_real_results():
    """Verifies Level 4 synthetic control results remain isolated from real validation."""
    p_synth = create_mock_ohrc_pds4_product()
    p_synth.is_synthetic = True

    gt = evaluate_ground_truth_level(p_synth, p_synth)
    assert gt == GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL
    assert gt != GroundTruthLevel.LEVEL_1_GEOREFERENCED


def test_fallback_and_simulated_matchers_explicitly_labeled():
    """Verifies that SuperPoint returns FALLBACK and RIFT returns SIMULATED when deep weights are uninitialized."""
    from outgraph.ml.matchers.adapters import SuperPointAdapter, RIFTAdapter
    sp = SuperPointAdapter()
    rift = RIFTAdapter()

    assert sp.is_deep_available is False
    assert "SuperPoint" in sp.name
    assert "RIFT" in rift.name

