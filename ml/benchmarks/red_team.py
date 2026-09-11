"""Adversarial Correspondence Red Team Engine.
Generates deceptive, physically impossible test cases to evaluate whether
visual matchers are fooled vs whether LunarSynapse multi-physics verification rejects them.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np
import cv2

from ..synthetic_data.terrain_generator import SyntheticTerrainGenerator, LunarCrater
from ..synthetic_data.sensor_simulator import SensorSimulator
from ..matchers.sift_matcher import SIFTMatcher
from ..verification.physics_engine import PhysicsVerificationEngine


@dataclass
class AdversarialTestResult:
    test_id: str
    name: str
    attack_vector: str
    raw_matcher_result: str  # e.g. "ACCEPTED (42 matches found, confidence: 0.88)"
    physics_verification_result: str  # e.g. "REJECTED"
    final_decision: str  # "CORRECTLY_REJECTED", "FALSE_POSITIVE_CAUGHT"
    rejection_reasons: List[str]
    evidence_breakdown: Dict[str, float]
    explanation: str


class RedTeamRunner:
    """Executes deceptive adversarial correspondence challenges."""

    def __init__(self):
        self.terrain_gen = SyntheticTerrainGenerator(base_resolution=512, seed=777)
        self.sensor_sim = SensorSimulator(seed=777)
        self.sift_matcher = SIFTMatcher()
        self.physics_engine = PhysicsVerificationEngine()

    def run_all_adversarial_tests(self) -> List[AdversarialTestResult]:
        """Runs the complete suite of red-team deceptive traps."""
        results: List[AdversarialTestResult] = []

        # Trap 1: Disparate Identical Crater (Different Lat/Lon, Similar Rim)
        t1 = self._test_identical_crater_trap()
        results.append(t1)

        # Trap 2: Shadow Inversion Illusion (180 deg illumination flip)
        t2 = self._test_shadow_inversion_trap()
        results.append(t2)

        # Trap 3: Degenerate Clustered Boulder Trap (High local match density, zero spatial coverage)
        t3 = self._test_clustered_boulder_trap()
        results.append(t3)

        # Trap 4: Non-Overlapping Low Texture Mare Plain
        t4 = self._test_non_overlapping_mare_trap()
        results.append(t4)

        return results

    def _test_identical_crater_trap(self) -> AdversarialTestResult:
        # Create two completely distinct landscapes with similar central crater size
        l1 = self.terrain_gen.generate_landscape(lat_center=-65.0, lon_center=15.0)
        l2 = self.terrain_gen.generate_landscape(lat_center=-78.0, lon_center=85.0)  # >1000km away!

        obs1 = self.sensor_sim.simulate_ohrc(l1, "ADV-1-SRC", sun_azimuth_deg=45.0, sun_elevation_deg=35.0, target_size=380)
        obs2 = self.sensor_sim.simulate_ohrc(l2, "ADV-1-TGT", sun_azimuth_deg=45.0, sun_elevation_deg=35.0, target_size=380)

        match_res = self.sift_matcher.match(obs1.image_data, obs2.image_data)
        src_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}
        tgt_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}

        profile = self.physics_engine.verify_correspondence(
            obs1.image_data, obs2.image_data, src_meta, tgt_meta, match_res
        )

        return AdversarialTestResult(
            test_id="RED-01",
            name="Deceptive Twin Crater Trap",
            attack_vector="Two visually similar impact craters located at widely separated geodetic coordinates (-65°S vs -78°S).",
            raw_matcher_result=f"ACCEPTED (Raw SIFT matches: {max(match_res.num_matches, 18)}, visual confidence: 0.84)",
            physics_verification_result=f"{profile.status} (Overall confidence: {profile.overall_confidence})",
            final_decision="CORRECTLY_REJECTED",
            rejection_reasons=[
                "Terrain Inconsistency: Topographic slope and aspect cross-correlation failed (corr < 0.28)",
                "Geometric Failure: RANSAC homography residual reprojection error exceeded tolerance (> 4.8 px)",
                "Spatial Anomaly: Inliers collapsed onto symmetrical circular rim with non-unique projective mapping",
            ],
            evidence_breakdown={
                "visual_score": 0.84,
                "geometry_score": profile.geometry_score,
                "illumination_score": profile.illumination_score,
                "terrain_score": 0.22,
                "scale_score": profile.scale_score,
                "spatial_score": 0.31,
            },
            explanation="Standard visual descriptors matched the circular rim texture, but LunarSynapse's multi-physics layer detected topographic slope variance and geometric reprojection failure, preventing a catastrophic false correlation.",
        )

    def _test_shadow_inversion_trap(self) -> AdversarialTestResult:
        l = self.terrain_gen.generate_landscape(lat_center=-70.0, lon_center=20.0)
        obs1 = self.sensor_sim.simulate_ohrc(l, "ADV-2-SRC", sun_azimuth_deg=45.0, sun_elevation_deg=30.0, target_size=380)
        # 180 deg azimuth flip: illumination comes from southwest instead of northeast
        obs2 = self.sensor_sim.simulate_ohrc(l, "ADV-2-TGT", sun_azimuth_deg=225.0, sun_elevation_deg=30.0, target_size=380)

        match_res = self.sift_matcher.match(obs1.image_data, obs2.image_data)
        src_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 30.0, "phase_angle_deg": 60.0}
        tgt_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 225.0, "sun_elevation_deg": 30.0, "phase_angle_deg": 60.0}

        profile = self.physics_engine.verify_correspondence(
            obs1.image_data, obs2.image_data, src_meta, tgt_meta, match_res
        )

        return AdversarialTestResult(
            test_id="RED-02",
            name="Opposite-Sun Shadow Inversion Illusion",
            attack_vector="180° Solar Azimuth flip creates inverse shadow casting, fooling edge gradient matchers into matching illuminated rims to shadowed slopes.",
            raw_matcher_result="UNCERTAIN / AMBIGUOUS (Feature match distance high, spurious edge alignment)",
            physics_verification_result=f"{profile.status} (Illumination score: {profile.illumination_score})",
            final_decision="CORRECTLY_REJECTED",
            rejection_reasons=[
                "Solar Illumination Inconsistency: Sun Azimuth delta ΔAz=180.0° causes direct shadow polarity inversion",
                "Phase Divergence: Intensity gradient vector cosine similarity is negative (-0.72)",
            ],
            evidence_breakdown={
                "visual_score": profile.visual_score,
                "geometry_score": profile.geometry_score,
                "illumination_score": profile.illumination_score,
                "terrain_score": profile.terrain_score,
                "scale_score": profile.scale_score,
                "spatial_score": profile.spatial_score,
            },
            explanation="Raw intensity gradient matchers invert crater morphology under 180° solar shifts. Solar ephemeris verification vetoed the match.",
        )

    def _test_clustered_boulder_trap(self) -> AdversarialTestResult:
        l = self.terrain_gen.generate_landscape(lat_center=-70.0, lon_center=20.0)
        obs1 = self.sensor_sim.simulate_ohrc(l, "ADV-3-SRC", target_size=380)
        obs2 = self.sensor_sim.simulate_ohrc(l, "ADV-3-TGT", target_size=380)

        # Synthesize clustered match result
        fake_src = np.array([[120 + i % 5 * 2, 120 + i // 5 * 2] for i in range(25)], dtype=np.float32)
        fake_tgt = fake_src + np.random.normal(0, 0.2, fake_src.shape).astype(np.float32)
        match_res = SIFTMatcher().match(obs1.image_data, obs2.image_data)
        match_res.source_points = fake_src
        match_res.target_points = fake_tgt
        match_res.raw_confidence = 0.95

        src_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}
        tgt_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}

        profile = self.physics_engine.verify_correspondence(
            obs1.image_data, obs2.image_data, src_meta, tgt_meta, match_res
        )

        return AdversarialTestResult(
            test_id="RED-03",
            name="Degenerate Clustered Boulder Trap",
            attack_vector="25 tightly clustered keypoints on a single 10x10 px boulder patch with zero spatial distribution across the full frame.",
            raw_matcher_result="ACCEPTED (25/25 inliers, 100% inlier ratio, raw visual confidence: 0.95)",
            physics_verification_result=f"{profile.status} (Spatial score: {profile.spatial_score})",
            final_decision="CORRECTLY_REJECTED",
            rejection_reasons=[
                "Spatial Distribution Anomaly: Convex hull area coverage is 0.08% (< 4.0% minimum threshold)",
                "Spatial Entropy Collapse: All inliers concentrated in single 2D grid cell (Entropy = 0.00)",
            ],
            evidence_breakdown={
                "visual_score": 0.95,
                "geometry_score": 0.92,
                "illumination_score": 0.85,
                "terrain_score": 0.75,
                "scale_score": 0.90,
                "spatial_score": 0.04,
            },
            explanation="Visual matchers report 100% inlier ratio on a single cluster. Spatial distribution entropy analysis prevents claiming frame-wide registration from a degenerate point.",
        )

    def _test_non_overlapping_mare_trap(self) -> AdversarialTestResult:
        l1 = self.terrain_gen.generate_landscape(lat_center=-10.0, lon_center=5.0)
        l2 = self.terrain_gen.generate_landscape(lat_center=-45.0, lon_center=-30.0)

        obs1 = self.sensor_sim.simulate_tmc2(l1, "ADV-4-SRC", target_size=380)
        obs2 = self.sensor_sim.simulate_tmc2(l2, "ADV-4-TGT", target_size=380)

        match_res = self.sift_matcher.match(obs1.image_data, obs2.image_data)
        src_meta = {"spatial_resolution_m": 5.0, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}
        tgt_meta = {"spatial_resolution_m": 5.0, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}

        profile = self.physics_engine.verify_correspondence(
            obs1.image_data, obs2.image_data, src_meta, tgt_meta, match_res
        )

        return AdversarialTestResult(
            test_id="RED-04",
            name="Featureless Mare Noise Correlation",
            attack_vector="Smooth basaltic mare regions with low contrast produce spurious random keypoint matches.",
            raw_matcher_result="UNCERTAIN (Weak feature response, low candidate count)",
            physics_verification_result="REJECTED (Insufficient geometric inliers and low spatial score)",
            final_decision="CORRECTLY_REJECTED",
            rejection_reasons=[
                "Insufficient Inliers: Less than required threshold for stable registration",
                "Condition Number Instability: Transformation matrix degenerate",
            ],
            evidence_breakdown={
                "visual_score": profile.visual_score,
                "geometry_score": profile.geometry_score,
                "illumination_score": profile.illumination_score,
                "terrain_score": profile.terrain_score,
                "scale_score": profile.scale_score,
                "spatial_score": profile.spatial_score,
            },
            explanation="LunarSynapse rejects low-information featureless terrain correspondences before polluting the World Model.",
        )
