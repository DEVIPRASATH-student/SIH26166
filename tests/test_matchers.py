"""Test Suite for Feature Matchers."""

import numpy as np
import pytest
from outgraph.ml.matchers.sift_matcher import SIFTMatcher
from outgraph.ml.matchers.orb_matcher import ORBMatcher
from outgraph.ml.matchers.adapters import SuperPointAdapter, LoFTRAdapter, RIFTAdapter, get_matcher
from outgraph.ml.synthetic_data.terrain_generator import SyntheticTerrainGenerator
from outgraph.ml.synthetic_data.sensor_simulator import SensorSimulator


@pytest.fixture
def sample_pair():
    gen = SyntheticTerrainGenerator(base_resolution=300, seed=42)
    landscape = gen.generate_landscape()
    sim = SensorSimulator(seed=42)
    obs1 = sim.simulate_ohrc(landscape, "TEST-1", sun_azimuth_deg=45.0, target_size=256)
    obs2 = sim.simulate_ohrc(landscape, "TEST-2", sun_azimuth_deg=50.0, target_size=256)
    return obs1.image_data, obs2.image_data


def test_sift_matcher_extraction_and_matching(sample_pair):
    img1, img2 = sample_pair
    matcher = SIFTMatcher()
    kps, desc = matcher.extract_features(img1)
    assert len(kps) > 10
    assert desc.shape[0] == len(kps)
    assert desc.shape[1] == 128

    res = matcher.match(img1, img2)
    assert res.num_matches > 0
    assert res.source_points.shape[1] == 2
    assert res.target_points.shape[1] == 2
    assert 0.0 <= res.raw_confidence <= 1.0


def test_orb_matcher(sample_pair):
    img1, img2 = sample_pair
    matcher = ORBMatcher()
    kps, desc = matcher.extract_features(img1)
    assert len(kps) > 10
    assert desc.shape[1] == 32

    res = matcher.match(img1, img2)
    assert res.num_matches >= 0


def test_adapter_fallbacks(sample_pair):
    img1, img2 = sample_pair
    sp_adapter = SuperPointAdapter()
    loftr_adapter = LoFTRAdapter()
    rift_adapter = RIFTAdapter()

    res_sp = sp_adapter.match(img1, img2)
    assert res_sp.algorithm_name == "SuperPoint-Adapter"

    res_loftr = loftr_adapter.match(img1, img2)
    assert res_loftr.algorithm_name == "LoFTR-Adapter"

    res_rift = rift_adapter.match(img1, img2)
    assert res_rift.algorithm_name == "RIFT-Adapter"


def test_matcher_factory():
    m1 = get_matcher("SIFT")
    assert isinstance(m1, SIFTMatcher)
    m2 = get_matcher("ORB")
    assert isinstance(m2, ORBMatcher)
    m3 = get_matcher("SuperPoint")
    assert isinstance(m3, SuperPointAdapter)
