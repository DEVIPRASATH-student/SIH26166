"""Unit and Integration Tests for Elevation-Bounded Target Corridor (Stage 3.4)."""

import pytest
import numpy as np

from outgraph.ml.geometry.ground_grid import GroundGrid
from outgraph.ml.geometry.dem_interface import DEMInterface
from outgraph.ml.geometry.terrain_geometry import TerrainGeometry
from outgraph.ml.geometry.grid_projection import GridProjector
from outgraph.ml.geometry.parallax_model import ParallaxModel, TMC2_PARALLAX_PARAMS, SensorParallaxParams
from outgraph.ml.geometry.target_corridor import (
    TargetCorridorCalculator,
    CorridorResult,
)


OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"
TMC2_CSV_REL = "data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv"


@pytest.fixture(scope="module")
def corridor_calc():
    """Provides initialized TargetCorridorCalculator on real datasets."""
    g_ohr = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    g_tmc = GroundGrid.from_csv(TMC2_CSV_REL, use_cache=True)
    dem = DEMInterface.load_default(use_cache=True)
    terrain_geo = TerrainGeometry(ground_grid=g_ohr, dem=dem)
    projector = GridProjector(source_grid=g_ohr, target_grid=g_tmc)

    return TargetCorridorCalculator(projector=projector, terrain_geo=terrain_geo)


@pytest.fixture
def synthetic_corridor_calc():
    """Constructs a synthetic corridor calculator with full 100% overlap."""
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

    return TargetCorridorCalculator(projector=proj, terrain_geo=t_geo, target_parallax=synth_parallax)



def test_synthetic_corridor_computation(synthetic_corridor_calc):
    """Verifies elevation-bounded corridor generation on overlapping geometry."""
    calc = synthetic_corridor_calc

    res = calc.compute_corridor(
        ohrc_pixel=50.0, ohrc_scan=50.0,
        elevation_margin_m=200.0,
    )

    assert res.is_valid is True
    assert res.rejection_reason is None
    assert np.isfinite(res.reference_tmc_pixel)
    assert np.isfinite(res.reference_tmc_scan)

    assert res.elevation_min_m == pytest.approx(-1700.0, abs=1.0)
    assert res.elevation_max_m == pytest.approx(-1300.0, abs=1.0)

    # Corridor bounds must bracket the reference point
    assert res.corridor_pixel_min <= res.corridor_pixel_max
    assert res.corridor_scan_min <= res.corridor_scan_max
    assert res.corridor_width_pixels >= 0.0

    # Test point containment
    assert calc.contains_point(res, res.reference_tmc_pixel, res.reference_tmc_scan) is True
    assert calc.contains_point(res, res.reference_tmc_pixel + 100.0, res.reference_tmc_scan) is False


def test_corridor_out_of_bounds_rejection(corridor_calc):
    """Verifies that invalid source coordinates produce structured rejections."""
    res = corridor_calc.compute_corridor(-10.0, 500.0)

    assert res.is_valid is False
    assert res.rejection_reason == "SOURCE_OUT_OF_BOUNDS"
    assert np.isnan(res.reference_tmc_pixel)


def test_corridor_real_ohrc_target_rejection(corridor_calc):
    """Verifies that OHRC points outside TMC-2 produce TARGET_OUTSIDE_CALIBRATED_SWATH."""
    # Western edge of OHRC (pixel 0, scan 0) is outside the TMC-2 convex hull
    res = corridor_calc.compute_corridor(0.0, 0.0)

    assert res.is_valid is False
    assert res.rejection_reason == "TARGET_OUTSIDE_CALIBRATED_SWATH"


def test_corridor_real_ohrc_boundary_clamping(corridor_calc):
    """Verifies that OHRC points falling on the western boundary of TMC-2 are flagged."""
    # Eastern edge of OHRC (pixel 11999, scan 0) falls on the boundary (p = 0.0)
    res = corridor_calc.compute_corridor(11999.0, 0.0)

    # Because reference projection is 0.0 (boundary clamped), the corridor is flagged
    assert res.reference_tmc_pixel == pytest.approx(0.0, abs=1e-2)
    assert res.rejection_reason == "CORRIDOR_CLAMPED_TO_WESTERN_BOUNDARY"


def test_corridor_batch_computation(synthetic_corridor_calc):
    """Verifies batched corridor computation across multiple coordinate points."""
    calc = synthetic_corridor_calc
    pixels = np.array([20.0, 50.0, 80.0])
    scans = np.array([20.0, 50.0, 80.0])

    batch = calc.compute_corridors_batch(pixels, scans, elevation_margin_m=100.0)

    assert len(batch) == 3
    for item in batch:
        assert isinstance(item, CorridorResult)
        assert item.is_valid is True
        assert item.corridor_width_pixels >= 0.0
