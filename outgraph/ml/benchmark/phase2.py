"""CLI Entry Point for Phase 2 Real-Data Correspondence Benchmark.
Run via:
    python -m outgraph.ml.benchmark.phase2 --all
    python -m outgraph.ml.benchmark.phase2 --pair REAL_OHRC_LRO_001 --matcher SIFT
    python -m outgraph.ml.benchmark.phase2 --synthetic
"""

import sys
import argparse
import json
import logging
from typing import List, Optional, Dict, Any


from .phase2_runner import Phase2BenchmarkRunner
from .pair_registry import RealDataPairRegistry, BenchmarkPair
from .ground_truth import GroundTruthLevel
from ..synthetic_data.terrain_generator import SyntheticTerrainGenerator
from ..synthetic_data.sensor_simulator import SensorSimulator
import cv2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("LunarSynapse.ML.Phase2CLI")


def ensure_synthetic_control_fixtures(data_root: str = "data/real") -> List[str]:
    """Generates synthetic control pair fixtures (Level 4) if no real data is available,
    allowing full end-to-end benchmark engine testing without fabricating real data identity.
    """
    synth_dir = "data/synthetic_controls"
    import os
    os.makedirs(synth_dir, exist_ok=True)

    src_path = os.path.join(synth_dir, "synth_ohrc_control.tif")
    tgt_path = os.path.join(synth_dir, "synth_lro_control.tif")

    if not (os.path.exists(src_path) and os.path.exists(tgt_path)):
        gen = SyntheticTerrainGenerator(base_resolution=512, seed=42)
        sim = SensorSimulator(seed=42)
        l = gen.generate_landscape(lat_center=-70.0, lon_center=20.0)

        obs1 = sim.simulate_ohrc(l, "SYNTH-CTRL-OHRC", target_size=380)
        obs2 = sim.simulate_ohrc(l, "SYNTH-CTRL-LRO", sun_azimuth_deg=60.0, target_size=380)

        cv2.imwrite(src_path, obs1.image_data)
        cv2.imwrite(tgt_path, obs2.image_data)

    return [src_path, tgt_path]


from .dataset_inventory import DatasetScanner


def main():
    parser = argparse.ArgumentParser(description="LunarSynapse Phase 2 — Real-Data Correspondence Baseline")
    parser.add_argument("--all", action="store_true", help="Run benchmark across all registered pairs")
    parser.add_argument("--real", action="store_true", help="Run benchmark strictly on real lunar data pairs")
    parser.add_argument("--pair", type=str, default=None, help="Specific pair ID to evaluate")
    parser.add_argument("--matcher", type=str, default=None, help="Specific matcher name (SIFT, ORB, SUPERPOINT, LOFTR, RIFT)")
    parser.add_argument("--synthetic", action="store_true", help="Include synthetic control pairs (Level 4 Ground Truth)")
    parser.add_argument("--output", type=str, default="results/phase2", help="Output directory for JSON/CSV results")
    args = parser.parse_args()

    # STEP 1: Scan Workspace Dataset Inventory
    scanner = DatasetScanner()
    inventory_items = scanner.scan_workspace()

    print("\n============================================================")
    print("WORKSPACE DATASET INVENTORY")
    print("============================================================")
    print(f"Total Candidate Files Scanned: {len(inventory_items)}")
    real_items = [i for i in inventory_items if i.is_real_data]
    print(f"Confirmed Real Lunar Products: {len(real_items)}")
    print("------------------------------------------------------------")
    if inventory_items:
        for item in inventory_items[:10]:
            print(f"File: {item.filename:<25} | Sensor: {item.sensor:<10} | GSD: {item.gsd_m:<10} | Size: {item.file_size_bytes} B | Real: {item.is_real_data}")
    else:
        print("No lunar dataset files found in workspace.")
    print("============================================================\n")

    runner = Phase2BenchmarkRunner(output_dir=args.output)
    matchers = [args.matcher] if args.matcher else ["SIFT", "ORB", "SUPERPOINT", "LOFTR", "RIFT"]

    if args.real:
        print("Executing Phase 2 Benchmark in --real mode...")
        results = runner.run_real_benchmark(matcher_names=matchers)
        print("\n============================================================")
        print("PHASE 2 REAL-DATA CORRESPONDENCE BASELINE SUMMARY")
        print("============================================================")
        print(f"Real Data Pairs Tested: {len(set(r['pair_id'] for r in results)) if results else 0}")
        print(f"Total Matcher Runs:     {len(results)}")
        print("------------------------------------------------------------")
        if not results:
            print("STATUS: NO REAL DATASETS FOUND IN data/real/.")
            print("To run real-data correspondence benchmarks, place local ISRO/LRO/SELENE products in data/real/.")
        else:
            for r in results:
                m = r["metrics"]
                print(f"Pair: {r['pair_id']:<24} | Matcher: {r['matcher']:<10} | GT: {r['ground_truth_level']:<30} | Status: {r['status']:<10} | Inliers: {m['geometric_inliers']:<3} | Error: {m['mean_reprojection_error_px']:.2f}px")
        print("============================================================\n")
        return

    # Default / --all execution
    registered_pairs = runner.registry.list_pairs()
    if len(registered_pairs) == 0:
        logger.warning("No real lunar data files found in data/real/. Registering synthetic benchmark control pair (Level 4 GT)...")
        src_path, tgt_path = ensure_synthetic_control_fixtures()

        control_pair = BenchmarkPair(
            pair_id="SYNTH_CTRL_OHRC_LRO_001",
            source_sensor="OHRC_SYNTH",
            target_sensor="LRO_NAC_SYNTH",
            source_product_id="synth_ohrc_control.tif",
            target_product_id="synth_lro_control.tif",
            source_file_path=src_path,
            target_file_path=tgt_path,
            priority_tier=1,
            expected_difficulty="medium",
            is_real_data=False,
            ground_truth_level=GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL,
            notes="Synthetic control pair for benchmark engine verification",
        )
        runner.registry.register_pair(control_pair)

    results = runner.run_benchmark(
        pair_id=args.pair,
        matcher_names=matchers,
        include_synthetic=True,
    )

    print("\n============================================================")
    print("PHASE 2 REAL-DATA CORRESPONDENCE BASELINE SUMMARY")
    print("============================================================")
    print(f"Total Evaluated Pairs: {len(set(r['pair_id'] for r in results))}")
    print(f"Total Matcher Runs:   {len(results)}")
    print("------------------------------------------------------------")
    for r in results:
        m = r["metrics"]
        print(f"Pair: {r['pair_id']:<24} | Matcher: {r['matcher']:<10} | GT: {r['ground_truth_level']:<30} | Status: {r['status']:<10} | Inliers: {m['geometric_inliers']:<3} | Error: {m['mean_reprojection_error_px']:.2f}px")
    print("============================================================\n")


if __name__ == "__main__":
    main()

