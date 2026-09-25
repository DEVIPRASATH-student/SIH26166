"""Unit and Integration Tests for Physically Constrained Candidate Engine (Stage 3.5)."""

import pytest
import numpy as np

from outgraph.ml.geometry.ground_grid import GroundGrid
from outgraph.ml.geometry.dem_interface import DEMInterface
from outgraph.ml.geometry.terrain_geometry import TerrainGeometry
from outgraph.ml.geometry.grid_projection import GridProjector
from outgraph.ml.geometry.parallax_model import ParallaxModel, TMC2_PARALLAX_PARAMS, SensorParallaxParams
from outgraph.ml.geometry.target_corridor import TargetCorridorCalculator
from outgraph.ml.matchers.physical_matcher import (
    PhysicalCandidateEngine,
    PhysicalCandidate,
)

OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"
TMC2_CSV_REL = "data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv"


@pytest.fixture(scope="module")
def real_engine():
    """Provides initialized PhysicalCandidateEngine on real datasets."""
    g_ohr = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    g_tmc = GroundGrid.from_csv(TMC2_CSV_REL, use_cache=True)
    dem = DEMInterface.load_default(use_cache=True)
    terrain_geo = TerrainGeometry(ground_grid=g_ohr, dem=dem)
    projector = GridProjector(source_grid=g_ohr, target_grid=g_tmc)
    corridor_calc = TargetCorridorCalculator(projector=projector, terrain_geo=terrain_geo)

    return PhysicalCandidateEngine(corridor_calc=corridor_calc)


@pytest.fixture
def synthetic_engine():
    """Provides PhysicalCandidateEngine on synthetic overlapping grids."""
    p1 = np.repeat(np.linspace(0, 99, 10), 10).astype(np.int32)
    s1 = np.tile(np.linspace(0, 99, 10), 10).astype(np.int32)
    lon1 = 20.0 + (p1 / 99.0) * 1.0
    lat1 = 0.0 + (s1 / 99.0) * 1.0

    p2 = np.repeat(np.linspace(0, 19, 5), 5).astype(np.int32)
    s2 = np.tile(np.linspace(0, 19, 5), 5).astype(np.int32)
    lon2 = 19.5 + (p2 / 19.0) * 2.0
    lat2 = -0.5 + (s2 / 19.0) * 2.0

    g_src = GroundGrid("src", p1, s1, lon1, lat1, True)
    g_tgt = GroundGrid("tgt", p2, s2, lon2, lat2, True)

    mock_dem = DEMInterface(
        elevation_grid=np.full((20, 20), -1500.0, dtype=np.float32),
        lat_min=-0.5, lat_max=1.5,
        lon_min=19.5, lon_max=21.5,
        resolution_ppd=10.0,
    )
    t_geo = TerrainGeometry(g_src, mock_dem)
    proj = GridProjector(g_src, g_tgt)

    synth_parallax = ParallaxModel(
        SensorParallaxParams(
            sensor_name="synth_tgt",
            spacecraft_altitude_km=100.0,
            ground_sampling_distance_m=10.0,
            total_samples=20,
            center_sample=9.5,
        )
    )
    corridor_calc = TargetCorridorCalculator(
        projector=proj, terrain_geo=t_geo, target_parallax=synth_parallax
    )
    return PhysicalCandidateEngine(corridor_calc=corridor_calc)


def test_physical_engine_accepts_valid_synthetic_candidate(synthetic_engine):
    """Verifies that a valid interior point passes all six physical gates."""
    cand = synthetic_engine.evaluate_candidate(source_pixel=50.0, source_scan=50.0)

    assert isinstance(cand, PhysicalCandidate)
    assert cand.is_accepted is True
    assert cand.rejection_reason is None
    assert np.isfinite(cand.predicted_target_pixel)
    assert np.isfinite(cand.predicted_target_scan)
    assert cand.corridor_width_m > 0.0


def test_physical_engine_rejects_gate1_source_out_of_bounds(real_engine):
    """Verifies Gate 1 rejection on negative/out-of-bounds source coordinates."""
    cand = real_engine.evaluate_candidate(source_pixel=-10.0, source_scan=500.0)

    assert cand.is_accepted is False
    assert cand.rejection_reason == "GATE1_SOURCE_OUT_OF_CALIBRATED_GRID"


def test_physical_engine_rejects_gate3_target_outside_swath(real_engine):
    """Verifies Gate 3 rejection when OHRC point falls outside TMC-2 triangulation."""
    # Western edge of OHRC (pixel 0, scan 0)
    cand = real_engine.evaluate_candidate(source_pixel=0.0, source_scan=0.0)

    assert cand.is_accepted is False
    assert cand.rejection_reason == "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH"


def test_physical_engine_rejects_gate4_boundary_clamped(real_engine):
    """Verifies Gate 4 rejection when target coordinate is clamped to swath edge."""
    # Eastern edge of OHRC (pixel 11999, scan 0) projects to boundary pixel 0.0
    cand = real_engine.evaluate_candidate(source_pixel=11999.0, source_scan=0.0)

    assert cand.is_accepted is False
    assert cand.rejection_reason == "GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY"


def test_physical_engine_rejects_all_real_candidates_due_to_gap(real_engine):
    """Verifies that 100% of real OHRC candidate points are rejected due to the physical footprint gap.

    Confirms that the engine refuses to fabricate artificial correspondence between adjacent swaths.
    """
    pixels = np.linspace(0.0, 11999.0, 5)
    scans = np.linspace(0.0, 78174.0, 5)
    P, S = np.meshgrid(pixels, scans)

    candidates = real_engine.evaluate_batch(P.ravel(), S.ravel())

    assert len(candidates) == 25
    accepted_count = sum(1 for c in candidates if c.is_accepted)
    # ZERO candidates must be accepted because swaths do not overlap
    assert accepted_count == 0

    reasons = [c.rejection_reason for c in candidates]
    assert "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH" in reasons
    assert "GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY" in reasons
