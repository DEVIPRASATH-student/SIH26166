"""Test Suite for Physics Verification Engine."""

import numpy as np
import pytest
from outgraph.ml.verification.geometry import GeometricVerifier
from outgraph.ml.verification.illumination import IlluminationVerifier
from outgraph.ml.verification.terrain import TerrainVerifier
from outgraph.ml.verification.scale_spatial import ScaleSpatialVerifier
from outgraph.ml.verification.physics_engine import PhysicsVerificationEngine
from outgraph.ml.matchers.sift_matcher import SIFTMatcher
from outgraph.ml.synthetic_data.terrain_generator import SyntheticTerrainGenerator
from outgraph.ml.synthetic_data.sensor_simulator import SensorSimulator


@pytest.fixture
def sim_data():
    gen = SyntheticTerrainGenerator(base_resolution=300, seed=42)
    landscape = gen.generate_landscape()
    sim = SensorSimulator(seed=42)
    obs1 = sim.simulate_ohrc(landscape, "OHRC-1", sun_azimuth_deg=45.0, target_size=256)
    obs2 = sim.simulate_ohrc(landscape, "OHRC-2", sun_azimuth_deg=50.0, target_size=256)
    return obs1, obs2


def test_geometric_verifier():
    verifier = GeometricVerifier(ransac_threshold_px=3.0)
    # Synthetic consistent points with slight shift
    src_pts = np.array([[50, 50], [150, 50], [150, 150], [50, 150], [100, 100], [80, 120]], dtype=np.float32)
    tgt_pts = src_pts + np.array([2.5, -1.5], dtype=np.float32)

    res = verifier.verify(src_pts, tgt_pts)
    assert res.is_valid is True
    assert res.num_inliers == 6
    assert res.inlier_ratio == 1.0
    assert res.mean_reprojection_error_px < 1.0
    assert 0.0 <= res.geometry_score <= 1.0


def test_illumination_verifier(sim_data):
    obs1, obs2 = sim_data
    verifier = IlluminationVerifier()
    src_meta = {"sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}
    tgt_meta = {"sun_azimuth_deg": 50.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}

    res = verifier.verify(obs1.image_data, obs2.image_data, src_meta, tgt_meta)
    assert res.is_valid is True
    assert res.solar_azimuth_delta_deg == 5.0
    assert 0.0 <= res.illumination_score <= 1.0


def test_scale_spatial_verifier():
    verifier = ScaleSpatialVerifier()
    # Well dispersed points
    src_pts = np.array([[20, 20], [200, 30], [220, 210], [30, 220], [120, 120]], dtype=np.float32)
    tgt_pts = src_pts + 1.0
    inliers = np.ones((5,), dtype=bool)

    res = verifier.verify(src_pts, tgt_pts, inliers, src_res_m=0.32, tgt_res_m=0.32, transform_matrix=np.eye(3))
    assert res.is_valid is True
    assert res.spatial_score > 0.30
    assert res.scale_score > 0.70


def test_physics_engine_pipeline(sim_data):
    obs1, obs2 = sim_data
    engine = PhysicsVerificationEngine()
    matcher = SIFTMatcher()
    match_res = matcher.match(obs1.image_data, obs2.image_data)

    src_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 45.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}
    tgt_meta = {"spatial_resolution_m": 0.32, "sun_azimuth_deg": 50.0, "sun_elevation_deg": 35.0, "phase_angle_deg": 55.0}

    profile = engine.verify_correspondence(
        obs1.image_data, obs2.image_data, src_meta, tgt_meta, match_res
    )
    assert 0.0 <= profile.overall_confidence <= 1.0
    assert profile.status in ["VERIFIED", "UNCERTAIN", "REJECTED"]
    assert 0.0 <= profile.visual_score <= 1.0
    assert 0.0 <= profile.geometry_score <= 1.0
    assert 0.0 <= profile.illumination_score <= 1.0
    assert 0.0 <= profile.terrain_score <= 1.0
