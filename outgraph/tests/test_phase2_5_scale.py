"""Unit and Integration Tests for Phase 2.5 Scale-Normalized Real Correspondence Experiment."""

import os
import json
import pytest
import numpy as np
from pathlib import Path

from outgraph.ml.data.preprocessing.scale_pyramid import ScalePyramidGenerator, compute_scale_ratio, PyramidLevel
from outgraph.ml.benchmark.phase2_5_runner import Phase2_5ScaleExperimentRunner
from outgraph.ml.data.fixtures.test_fixtures import create_mock_ohrc_pds4_product, create_mock_iirs_pds4_product
from outgraph.ml.data.models import ValueStatus, ValidationResult


def test_scale_ratio_calculation():
    """Verifies physical GSD scale ratio calculation for OHRC vs TMC-2."""
    ohrc_gsd = 0.26
    tmc_gsd = 6.07
    ratio = compute_scale_ratio(ohrc_gsd, tmc_gsd)
    assert pytest.approx(ratio, 0.001) == 23.34615
    assert ratio > 1.0

    with pytest.raises(ValueError):
        compute_scale_ratio(0.0, 6.07)


def test_effective_gsd_calculation():
    """Verifies effective GSD calculation per pyramid scale level."""
    ohrc_gsd = 0.26
    scale_factors = [1.0, 2.0, 4.0, 8.0, 16.0, 23.34615]
    effective_gsds = [ohrc_gsd * sf for sf in scale_factors]

    assert effective_gsds[0] == 0.26
    assert pytest.approx(effective_gsds[1], 0.01) == 0.52
    assert pytest.approx(effective_gsds[2], 0.01) == 1.04
    assert pytest.approx(effective_gsds[3], 0.01) == 2.08
    assert pytest.approx(effective_gsds[4], 0.01) == 4.16
    assert pytest.approx(effective_gsds[5], 0.01) == 6.07


def test_pyramid_generation_and_dimensions(tmp_path):
    """Verifies anti-aliased image pyramid downsampling and dimensions."""
    product = create_mock_ohrc_pds4_product()
    # Create synthetic mock raster for testing pyramid generator
    product.raster_data = np.ones((1000, 1000), dtype=np.uint8) * 128
    product.metadata.gsd_m = 0.26
    product.metadata.value_statuses["gsd_m"] = ValueStatus.KNOWN

    generator = ScalePyramidGenerator(output_dir=str(tmp_path / "derived"))
    levels = generator.generate_pyramid(product, target_gsd_m=6.07)

    assert len(levels) == 6
    assert levels[0].scale_factor == 1.0
    assert levels[0].lines == 1000
    assert levels[0].samples == 1000

    # Check downsampled dimensions at 2x and 4x
    assert levels[1].lines == 500
    assert levels[1].samples == 500
    assert levels[2].lines == 250
    assert levels[2].samples == 250

    # Check TMC-equivalent level
    assert pytest.approx(levels[5].scale_factor, 0.01) == 23.35
    assert os.path.exists(levels[1].derived_image_path)


def test_derived_data_provenance(tmp_path):
    """Verifies DERIVED_FROM_REAL_DATA = TRUE tag in derived product provenance."""
    product = create_mock_ohrc_pds4_product()
    product.raster_data = np.ones((400, 400), dtype=np.uint8) * 100
    product.metadata.gsd_m = 0.26

    generator = ScalePyramidGenerator(output_dir=str(tmp_path / "derived"))
    levels = generator.generate_pyramid(product, target_gsd_m=6.07)

    derived_prod = levels[1].derived_product
    history = derived_prod.provenance.processing_history
    assert len(history) > 0

    transform_step = history[-1]
    assert transform_step["step"] == "SCALE_NORMALIZATION_DOWNSAMPLING"
    assert transform_step["parameters"]["DERIVED_FROM_REAL_DATA"] is True
    assert transform_step["parameters"]["original_gsd_m"] == 0.26


def test_original_data_immutability(tmp_path):
    """Verifies original raw products in data/real are not overwritten during pyramid generation."""
    dummy_orig = tmp_path / "data_real" / "ohrc.img"
    dummy_orig.parent.mkdir(parents=True, exist_ok=True)
    dummy_orig.write_bytes(b"ORIGINAL_REAL_BYTES_12345")

    product = create_mock_ohrc_pds4_product()
    product.file_path = dummy_orig
    product.raster_data = np.ones((200, 200), dtype=np.uint8) * 200
    product.metadata.gsd_m = 0.26

    generator = ScalePyramidGenerator(output_dir=str(tmp_path / "derived"))
    generator.generate_pyramid(product, target_gsd_m=6.07)

    # Original bytes must be completely unchanged
    assert dummy_orig.read_bytes() == b"ORIGINAL_REAL_BYTES_12345"


def test_phase2_5_runner_execution(tmp_path):
    """Verifies Phase 2.5 scale experiment runner outputs JSON & CSV results and decision logic."""
    data_root = "data/real"
    if not Path(data_root).exists():
        repo_root = Path(__file__).resolve().parents[2]
        if (repo_root / "data" / "real").exists():
            data_root = str(repo_root / "data" / "real")

    runner = Phase2_5ScaleExperimentRunner(
        output_dir=str(tmp_path / "results"),
        derived_data_dir=str(tmp_path / "derived"),
        data_root=data_root,
    )
    res = runner.run_experiment(matcher_names=["SIFT"])

    assert res["status"] == "COMPLETED"
    assert "scale_ratio" in res
    assert "final_decision" in res

    summary_path = tmp_path / "results" / "scale_experiment_summary.json"
    results_path = tmp_path / "results" / "scale_experiment_results.json"
    csv_path = tmp_path / "results" / "scale_experiment_results.csv"

    assert summary_path.exists()
    assert results_path.exists()
    assert csv_path.exists()

    with open(summary_path, "r") as f:
        data = json.load(f)
    assert data["final_decision"]["decision_code"] in [
        "SCALE_EFFECT_SUPPORTED",
        "SCALE_EFFECT_NOT_SUPPORTED",
        "INCONCLUSIVE",
        "SCALE_EFFECT_OBSERVED_BUT_GEOMETRICALLY_UNSTABLE",
        "GEOMETRICALLY_STABLE_CORRESPONDENCE_FOUND",
    ]
