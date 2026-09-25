"""Phase 2 Real-Data Correspondence Benchmark Runner Engine.

Executes scientifically defensible correspondence evaluation on real lunar observations
and benchmark synthetic control pairs using existing feature matchers (SIFT, ORB, Adapters)
and geometric/scale verification pipelines.
"""

import os
import time
import json
import csv
import numpy as np
import cv2
from typing import Dict, List, Optional, Tuple, Any
import logging

from .pair_registry import RealDataPairRegistry, BenchmarkPair
from .ground_truth import evaluate_ground_truth_level, GroundTruthLevel
from .metrics import BenchmarkMetrics, MatcherImplementationStatus
from .failure_classifier import classify_correspondence_failure, FailureAnalysisResult, CorrespondenceOutcome
from ..data.ingestion.factory import ProductIngestionEngine
from ..data.preprocessing.interface import SensorAwarePreprocessor
from ..data.models import LunarProduct, ValueStatus
from ..matchers.sift_matcher import SIFTMatcher
from ..matchers.orb_matcher import ORBMatcher
from ..matchers.adapters import SuperPointAdapter, LoFTRAdapter, RIFTAdapter, get_matcher
from ..verification.geometry import GeometricVerifier
from ..verification.scale_spatial import ScaleSpatialVerifier

logger = logging.getLogger("LunarSynapse.ML.Phase2Runner")


class Phase2BenchmarkRunner:
    """Benchmark runner executing Phase 2 real-data correspondence baseline evaluation."""

    def __init__(self, output_dir: str = "results/phase2", data_root: str = "data/real"):
        self.output_dir = output_dir
        self.data_root = data_root
        self.registry = RealDataPairRegistry(data_root=data_root)
        self.ingestion_engine = ProductIngestionEngine()
        self.preprocessor = SensorAwarePreprocessor()
        self.geo_verifier = GeometricVerifier(ransac_threshold_px=3.5, min_inliers=6, max_reprojection_error=4.0)
        self.scale_verifier = ScaleSpatialVerifier()

        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "visualizations"), exist_ok=True)

    def run_benchmark(
        self,
        pair_id: Optional[str] = None,
        matcher_names: Optional[List[str]] = None,
        include_synthetic: bool = True,
    ) -> List[Dict[str, Any]]:
        """Executes Phase 2 benchmark across selected pairs and matchers."""
        if matcher_names is None:
            matcher_names = ["SIFT", "ORB", "SUPERPOINT", "LOFTR", "RIFT"]

        # Ensure synthetic control pair is registered if no pairs exist
        if len(self.registry.list_pairs()) == 0 and include_synthetic:
            self._ensure_synthetic_control_pair()

        # Select target pairs
        if pair_id:
            pair = self.registry.get_pair(pair_id)
            pairs = [pair] if pair else []
        else:
            pairs = self.registry.list_pairs()

        if not include_synthetic:
            pairs = [p for p in pairs if p.is_real_data]

        results: List[Dict[str, Any]] = []

        logger.info(f"Running Phase 2 Correspondence Benchmark on {len(pairs)} pair(s) across {len(matcher_names)} matcher(s)...")

        for pair in pairs:
            for matcher_name in matcher_names:
                res = self.evaluate_pair(pair, matcher_name)
                results.append(res)

        self._save_results(results)
        return results

    def run_real_benchmark(
        self,
        matcher_names: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Executes Phase 2 correspondence benchmark strictly on real lunar data pairs."""
        if matcher_names is None:
            matcher_names = ["SIFT", "ORB", "SUPERPOINT", "LOFTR", "RIFT"]

        real_pairs = self.registry.list_pairs(real_only=True)
        results: List[Dict[str, Any]] = []

        real_out_dir = self.output_dir
        os.makedirs(os.path.join(real_out_dir, "visualizations", "real"), exist_ok=True)

        if len(real_pairs) == 0:
            logger.warning("No real lunar data pairs registered in data/real/. Writing real benchmark summary with NO_REAL_DATA_FOUND status.")
            summary_path = os.path.join(real_out_dir, "real_benchmark_summary.json")
            summary = {
                "real_data_executed": False,
                "status": "NO_REAL_DATA_FOUND",
                "message": "No real lunar data files found in data/real/. Please place local ISRO/LRO/SELENE products in data/real/ to execute real-data correspondence baseline.",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)

            # Write empty JSON & CSV results
            with open(os.path.join(real_out_dir, "real_benchmark_results.json"), "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

            with open(os.path.join(real_out_dir, "real_benchmark_results.csv"), "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["pair_id", "matcher", "source_sensor", "target_sensor", "is_real_data", "status"])

            with open(os.path.join(real_out_dir, "real_failure_analysis.json"), "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

            return []

        logger.info(f"Running Phase 2 Real-Data Correspondence Benchmark on {len(real_pairs)} pair(s)...")
        for pair in real_pairs:
            for matcher_name in matcher_names:
                res = self.evaluate_pair(pair, matcher_name)
                results.append(res)

        self._save_real_results(results)
        return results

    def _save_real_results(self, results: List[Dict[str, Any]]):
        """Saves real-data benchmark results into dedicated real_* JSON and CSV files."""
        # 1. real_benchmark_results.json
        json_path = os.path.join(self.output_dir, "real_benchmark_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        # 2. real_benchmark_results.csv
        csv_path = os.path.join(self.output_dir, "real_benchmark_results.csv")
        fieldnames = [
            "pair_id", "matcher", "source_sensor", "target_sensor", "is_real_data",
            "ground_truth_level", "status", "matcher_implementation_status",
            "candidate_matches", "inliers", "inlier_ratio", "mean_reprojection_error_px",
            "spatial_coverage_ratio", "homography_condition_number", "scale_ratio_status",
            "dominant_failure", "processing_time_sec",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                m = r.get("metrics", {})
                fa = r.get("failure_analysis", {})
                writer.writerow({
                    "pair_id": r.get("pair_id"),
                    "matcher": r.get("matcher"),
                    "source_sensor": r.get("source_sensor"),
                    "target_sensor": r.get("target_sensor"),
                    "is_real_data": r.get("is_real_data"),
                    "ground_truth_level": r.get("ground_truth_level"),
                    "status": r.get("status"),
                    "matcher_implementation_status": m.get("matcher_implementation_status"),
                    "candidate_matches": m.get("candidate_matches"),
                    "inliers": m.get("geometric_inliers"),
                    "inlier_ratio": m.get("inlier_ratio"),
                    "mean_reprojection_error_px": m.get("mean_reprojection_error_px"),
                    "spatial_coverage_ratio": m.get("spatial_coverage_ratio"),
                    "homography_condition_number": m.get("homography_condition_number"),
                    "scale_ratio_status": m.get("scale_ratio_status"),
                    "dominant_failure": fa.get("dominant_failure"),
                    "processing_time_sec": m.get("total_processing_time_sec"),
                })

        # 3. real_benchmark_summary.json
        summary_path = os.path.join(self.output_dir, "real_benchmark_summary.json")
        summary = {
            "real_data_executed": True,
            "total_real_pairs_evaluated": len(set(r["pair_id"] for r in results)),
            "total_real_runs": len(results),
            "status_counts": {
                "ACCEPTED": sum(1 for r in results if r["status"] == "ACCEPTED"),
                "REJECTED": sum(1 for r in results if r["status"] == "REJECTED"),
                "AMBIGUOUS": sum(1 for r in results if r["status"] == "AMBIGUOUS"),
                "INSUFFICIENT_EVIDENCE": sum(1 for r in results if r["status"] == "INSUFFICIENT_EVIDENCE"),
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        # 4. real_failure_analysis.json
        failure_path = os.path.join(self.output_dir, "real_failure_analysis.json")
        failures = [
            {
                "pair_id": r["pair_id"],
                "matcher": r["matcher"],
                "status": r["status"],
                "failure_analysis": r.get("failure_analysis"),
            }
            for r in results
            if r["status"] != "ACCEPTED"
        ]
        with open(failure_path, "w", encoding="utf-8") as f:
            json.dump(failures, f, indent=2, default=str)


    def _ensure_synthetic_control_pair(self):
        """Creates synthetic control pair (Level 4 GT) fixture if no pairs exist in registry."""
        synth_dir = os.path.join(self.output_dir, "synthetic_controls")
        os.makedirs(synth_dir, exist_ok=True)
        src_path = os.path.join(synth_dir, "synth_ohrc_control.tif")
        tgt_path = os.path.join(synth_dir, "synth_lro_control.tif")

        if not (os.path.exists(src_path) and os.path.exists(tgt_path)):
            from ..synthetic_data.terrain_generator import SyntheticTerrainGenerator
            from ..synthetic_data.sensor_simulator import SensorSimulator
            gen = SyntheticTerrainGenerator(base_resolution=512, seed=42)
            sim = SensorSimulator(seed=42)
            l = gen.generate_landscape(lat_center=-70.0, lon_center=20.0)

            obs1 = sim.simulate_ohrc(l, "SYNTH-CTRL-OHRC", target_size=380)
            obs2 = sim.simulate_ohrc(l, "SYNTH-CTRL-LRO", sun_azimuth_deg=60.0, target_size=380)

            cv2.imwrite(src_path, obs1.image_data)
            cv2.imwrite(tgt_path, obs2.image_data)

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
        self.registry.register_pair(control_pair)


    def evaluate_pair(self, pair: BenchmarkPair, matcher_name: str) -> Dict[str, Any]:
        """Evaluates a single pair with a specific feature matcher."""
        t_start = time.time()

        # STEP 1 & 2: Load products through Phase 1 Ingestion
        t_pre_start = time.time()
        try:
            source_product = self.ingestion_engine.ingest_product(pair.source_file_path)
            target_product = self.ingestion_engine.ingest_product(pair.target_file_path)
        except Exception as e:
            logger.error(f"Ingestion failed for pair {pair.pair_id}: {e}")

            metrics = BenchmarkMetrics(
                matcher_name=matcher_name,
                matcher_implementation_status=MatcherImplementationStatus.UNAVAILABLE,
            )
            return {
                "pair_id": pair.pair_id,
                "matcher": matcher_name,
                "is_real_data": pair.is_real_data,
                "ground_truth_level": pair.ground_truth_level.to_string(),
                "status": CorrespondenceOutcome.REJECTED.value,
                "rejection_reason": f"Product Ingestion Failure: {e}",
                "metrics": metrics.to_dict(),
                "failure_analysis": {
                    "outcome": CorrespondenceOutcome.REJECTED.value,
                    "dominant_failure": "COMPUTATIONAL_FAILURE",
                    "explanation": f"Failed to ingest input products: {e}",
                },
                "provenance": pair.provenance,
            }

        # Determine Ground Truth Level
        gt_level = evaluate_ground_truth_level(source_product, target_product, pair.ground_truth_level)

        # STEP 4: Sensor-Aware Preprocessing Views (Non-destructive 8-bit analysis view)
        # Select band 0 for IIRS with explicit band tracking
        selected_band_idx = 0
        src_view, _ = self.preprocessor.extract_correspondence_ready_view(source_product, selected_band=selected_band_idx)
        tgt_view, _ = self.preprocessor.extract_correspondence_ready_view(target_product, selected_band=selected_band_idx)


        t_pre_end = time.time()
        preprocessing_time = t_pre_end - t_pre_start

        # STEP 5: Run Feature Matchers & Determine Implementation Status
        t_match_start = time.time()
        matcher_obj = get_matcher(matcher_name)

        # Check implementation status
        impl_status = MatcherImplementationStatus.REAL
        if isinstance(matcher_obj, (SuperPointAdapter, LoFTRAdapter)):
            if not getattr(matcher_obj, "is_deep_available", False):
                impl_status = MatcherImplementationStatus.FALLBACK
        elif isinstance(matcher_obj, RIFTAdapter):
            impl_status = MatcherImplementationStatus.SIMULATED

        try:
            match_res = matcher_obj.match(src_view, tgt_view)
            src_kps, src_descs = matcher_obj.extract_features(src_view)
            tgt_kps, tgt_descs = matcher_obj.extract_features(tgt_view)
        except Exception as e:
            logger.error(f"Matcher {matcher_name} failed on pair {pair.pair_id}: {e}")
            t_match_end = time.time()
            metrics = BenchmarkMetrics(
                matcher_name=matcher_name,
                matcher_implementation_status=MatcherImplementationStatus.UNAVAILABLE,
                preprocessing_time_sec=preprocessing_time,
                matching_time_sec=t_match_end - t_match_start,
                total_processing_time_sec=time.time() - t_start,
            )
            return {
                "pair_id": pair.pair_id,
                "matcher": matcher_name,
                "is_real_data": pair.is_real_data,
                "ground_truth_level": gt_level.to_string(),
                "status": CorrespondenceOutcome.REJECTED.value,
                "rejection_reason": f"Matcher Execution Error: {e}",
                "metrics": metrics.to_dict(),
                "failure_analysis": {
                    "outcome": CorrespondenceOutcome.REJECTED.value,
                    "dominant_failure": "COMPUTATIONAL_FAILURE",
                    "explanation": f"Matcher execution failed: {e}",
                },
                "provenance": pair.provenance,
            }

        t_match_end = time.time()
        matching_time = t_match_end - t_match_start

        # STEP 6: Geometric & Scale Verification
        t_verif_start = time.time()

        geo_res = self.geo_verifier.verify(
            source_pts=match_res.source_points,
            target_pts=match_res.target_points,
            image_shape=src_view.shape[:2],
        )

        # Handle GSD & Scale Ratio (NEVER calculate fabricated scale ratio if GSD is UNKNOWN!)
        src_gsd = source_product.metadata.gsd_m
        tgt_gsd = target_product.metadata.gsd_m
        src_gsd_status = source_product.metadata.value_statuses.get("gsd_m", ValueStatus.UNKNOWN)
        tgt_gsd_status = target_product.metadata.value_statuses.get("gsd_m", ValueStatus.UNKNOWN)

        if src_gsd_status == ValueStatus.KNOWN and tgt_gsd_status == ValueStatus.KNOWN and src_gsd and tgt_gsd:
            gsd_status_str = "KNOWN"
            scale_ratio = float(src_gsd / tgt_gsd)
            scale_status_str = "KNOWN"
            src_res_for_verif = src_gsd
            tgt_res_for_verif = tgt_gsd
        else:
            gsd_status_str = "UNKNOWN"
            scale_ratio = None
            scale_status_str = "UNKNOWN"
            src_res_for_verif = 1.0
            tgt_res_for_verif = 1.0

        scale_res = self.scale_verifier.verify(
            src_pts=match_res.source_points,
            tgt_pts=match_res.target_points,
            inlier_mask=geo_res.inlier_mask,
            src_res_m=src_res_for_verif,
            tgt_res_m=tgt_res_for_verif,
            transform_matrix=geo_res.transform_matrix,
            image_shape=src_view.shape[:2],
        )

        t_verif_end = time.time()
        verification_time = t_verif_end - t_verif_start
        total_time = time.time() - t_start

        # Calculate RMSE & Reprojection Error for Inliers
        if geo_res.num_inliers >= 4 and geo_res.inlier_mask is not None:
            inlier_src = match_res.source_points[geo_res.inlier_mask]
            inlier_tgt = match_res.target_points[geo_res.inlier_mask]
            if geo_res.transform_matrix is not None:
                src_homo = np.hstack([inlier_src, np.ones((len(inlier_src), 1), dtype=np.float32)])
                projected = (geo_res.transform_matrix @ src_homo.T).T
                projected_pts = projected[:, :2] / np.maximum(projected[:, 2:3], 1e-7)
                sq_errors = np.sum((projected_pts - inlier_tgt) ** 2, axis=1)
                rmse_val = float(np.sqrt(np.mean(sq_errors)))
                median_err = float(np.median(np.sqrt(sq_errors)))
            else:
                rmse_val = 999.0
                median_err = 999.0
        else:
            rmse_val = 999.0
            median_err = 999.0

        # Build BenchmarkMetrics Object
        metrics = BenchmarkMetrics(
            keypoints_source=len(src_kps),
            keypoints_target=len(tgt_kps),
            candidate_matches=match_res.num_matches,
            ratio_test_matches=match_res.num_matches,
            geometric_inliers=geo_res.num_inliers,
            inlier_ratio=geo_res.inlier_ratio,
            mean_reprojection_error_px=geo_res.mean_reprojection_error_px,
            median_reprojection_error_px=median_err,
            rmse_px=rmse_val,
            homography_condition_number=geo_res.condition_number,
            spatial_coverage_ratio=scale_res.convex_hull_area_ratio,
            convex_hull_area_ratio=scale_res.convex_hull_area_ratio,
            spatial_entropy=scale_res.spatial_entropy,
            native_gsd_source_m=src_gsd,
            native_gsd_target_m=tgt_gsd,
            gsd_status=gsd_status_str,
            estimated_scale_ratio=scale_ratio,
            scale_ratio_status=scale_status_str,
            feature_ambiguity=float(1.0 - match_res.raw_confidence),
            feature_sparsity=float(1.0 - np.clip(len(src_kps) / 2000.0, 0.0, 1.0)),
            overlap_confidence=float(geo_res.geometry_score),
            matcher_name=matcher_name,
            matcher_implementation_status=impl_status,
            preprocessing_time_sec=preprocessing_time,
            matching_time_sec=matching_time,
            verification_time_sec=verification_time,
            total_processing_time_sec=total_time,
        )

        # STEP 9: Outcome & Failure Classification
        failure_res = classify_correspondence_failure(
            source_product=source_product,
            target_product=target_product,
            metrics=metrics,
            min_inliers=self.geo_verifier.min_inliers,
            min_inlier_ratio=self.geo_verifier.min_inlier_ratio,
            max_reprojection_error=self.geo_verifier.max_reprojection_error,
            min_spatial_coverage=self.scale_verifier.min_spatial_coverage,
        )


        # Draw Visual Debugging Outputs
        self._generate_visualization(pair, matcher_name, src_view, tgt_view, match_res, geo_res.inlier_mask)

        # Detailed IIRS spectral band documentation metadata
        iirs_info = {}
        if "IIRS" in (source_product.metadata.instrument or "").upper() or "IIRS" in (target_product.metadata.instrument or "").upper():
            iirs_info = {
                "iirs_single_band_baseline": True,
                "selected_band_index": selected_band_idx,
                "multispectral_claim": "UNSUPPORTED — Single 2D slice extracted for baseline matching",
            }

        return {
            "pair_id": pair.pair_id,
            "matcher": matcher_name,
            "source_sensor": pair.source_sensor,
            "target_sensor": pair.target_sensor,
            "is_real_data": pair.is_real_data,
            "ground_truth_level": gt_level.to_string(),
            "status": failure_res.outcome.value,
            "rejection_reason": failure_res.rejection_reasons[0] if failure_res.rejection_reasons else None,
            "metrics": metrics.to_dict(),
            "failure_analysis": failure_res.to_dict(),
            "iirs_metadata": iirs_info,
            "provenance": {
                "source": source_product.provenance.dict(),
                "target": target_product.provenance.dict(),
            },
        }

    def _generate_visualization(
        self,
        pair: BenchmarkPair,
        matcher_name: str,
        src_view: np.ndarray,
        tgt_view: np.ndarray,
        match_res: Any,
        inlier_mask: Optional[np.ndarray],
    ):
        """Draws visual match side-by-side debugging image."""
        try:
            h1, w1 = src_view.shape[:2]
            h2, w2 = tgt_view.shape[:2]
            vis_h = max(h1, h2)
            vis_w = w1 + w2
            vis_img = np.zeros((vis_h, vis_w, 3), dtype=np.uint8)

            src_rgb = cv2.cvtColor(src_view, cv2.COLOR_GRAY2BGR) if src_view.ndim == 2 else src_view
            tgt_rgb = cv2.cvtColor(tgt_view, cv2.COLOR_GRAY2BGR) if tgt_view.ndim == 2 else tgt_view

            vis_img[:h1, :w1] = src_rgb
            vis_img[:h2, w1 : w1 + w2] = tgt_rgb

            if match_res.num_matches > 0:
                for idx, (p1, p2) in enumerate(zip(match_res.source_points, match_res.target_points)):
                    pt1 = (int(p1[0]), int(p1[1]))
                    pt2 = (int(p2[0]) + w1, int(p2[1]))
                    is_inlier = inlier_mask[idx] if inlier_mask is not None and idx < len(inlier_mask) else False

                    color = (0, 255, 0) if is_inlier else (0, 0, 255)
                    cv2.circle(vis_img, pt1, 3, color, -1)
                    cv2.circle(vis_img, pt2, 3, color, -1)
                    if is_inlier or match_res.num_matches < 30:
                        cv2.line(vis_img, pt1, pt2, color, 1)

            filename = f"{pair.pair_id}_{matcher_name}_vis.jpg"
            save_path = os.path.join(self.output_dir, "visualizations", filename)
            cv2.imwrite(save_path, vis_img)
        except Exception as e:
            logger.warning(f"Failed to generate visualization for {pair.pair_id}: {e}")

    def _save_results(self, results: List[Dict[str, Any]]):
        """Saves benchmark results into JSON and CSV files."""
        # 1. Save full benchmark_results.json
        json_path = os.path.join(self.output_dir, "benchmark_results.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)

        # 2. Save CSV summary benchmark_results.csv
        csv_path = os.path.join(self.output_dir, "benchmark_results.csv")
        fieldnames = [
            "pair_id",
            "matcher",
            "source_sensor",
            "target_sensor",
            "is_real_data",
            "ground_truth_level",
            "status",
            "matcher_implementation_status",
            "candidate_matches",
            "inliers",
            "inlier_ratio",
            "mean_reprojection_error_px",
            "spatial_coverage_ratio",
            "homography_condition_number",
            "scale_ratio_status",
            "dominant_failure",
            "processing_time_sec",
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in results:
                m = r.get("metrics", {})
                fa = r.get("failure_analysis", {})
                writer.writerow({
                    "pair_id": r.get("pair_id"),
                    "matcher": r.get("matcher"),
                    "source_sensor": r.get("source_sensor"),
                    "target_sensor": r.get("target_sensor"),
                    "is_real_data": r.get("is_real_data"),
                    "ground_truth_level": r.get("ground_truth_level"),
                    "status": r.get("status"),
                    "matcher_implementation_status": m.get("matcher_implementation_status"),
                    "candidate_matches": m.get("candidate_matches"),
                    "inliers": m.get("geometric_inliers"),
                    "inlier_ratio": m.get("inlier_ratio"),
                    "mean_reprojection_error_px": m.get("mean_reprojection_error_px"),
                    "spatial_coverage_ratio": m.get("spatial_coverage_ratio"),
                    "homography_condition_number": m.get("homography_condition_number"),
                    "scale_ratio_status": m.get("scale_ratio_status"),
                    "dominant_failure": fa.get("dominant_failure"),
                    "processing_time_sec": m.get("total_processing_time_sec"),
                })

        # 3. Save benchmark_summary.json
        summary_path = os.path.join(self.output_dir, "benchmark_summary.json")
        real_executed = any(r.get("is_real_data", False) for r in results)
        summary = {
            "total_pairs_evaluated": len(set(r["pair_id"] for r in results)),
            "total_runs": len(results),
            "real_data_executed": real_executed,
            "status_counts": {
                "ACCEPTED": sum(1 for r in results if r["status"] == "ACCEPTED"),
                "REJECTED": sum(1 for r in results if r["status"] == "REJECTED"),
                "AMBIGUOUS": sum(1 for r in results if r["status"] == "AMBIGUOUS"),
                "INSUFFICIENT_EVIDENCE": sum(1 for r in results if r["status"] == "INSUFFICIENT_EVIDENCE"),
            },
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, default=str)

        # 4. Save failure_analysis.json
        failure_path = os.path.join(self.output_dir, "failure_analysis.json")
        failures = [
            {
                "pair_id": r["pair_id"],
                "matcher": r["matcher"],
                "status": r["status"],
                "failure_analysis": r.get("failure_analysis"),
            }
            for r in results
            if r["status"] != "ACCEPTED"
        ]
        with open(failure_path, "w", encoding="utf-8") as f:
            json.dump(failures, f, indent=2, default=str)


        logger.info(f"Phase 2 benchmark results saved to {self.output_dir}/")
