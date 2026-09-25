"""Test Suite for Stage 5.5: Knowledge-Gap Systematic Benchmark."""

import pytest
import os
import json

from outgraph.ml.world_model.gap_benchmark import KnowledgeGapBenchmark


def test_knowledge_gap_benchmark_execution(tmp_path):
    out_file = str(tmp_path / "knowledge_gap_benchmark.json")
    result = KnowledgeGapBenchmark.run_benchmark(output_json_path=out_file)

    assert result["all_passed"] is True
    assert result["total_scenarios"] == 8
    assert result["passed_scenarios"] == 8
    assert result["pass_rate"] == 1.0

    # Verify file saved
    assert os.path.exists(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_scenarios"] == 8

    # Verify Footprint Non-Overlap Scenario (Scenario 7)
    s7 = [s for s in data["scenarios"] if s["scenario_index"] == 7][0]
    assert s7["target_gap_type"] == "FOOTPRINT_NON_OVERLAP"
    assert s7["blocking_reason"] == "PHYSICAL_FOOTPRINT_SEPARATION"
    assert s7["passed"] is True
