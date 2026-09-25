"""Unit and Integration Tests for Reference-Datum Grid-to-Grid Projection (Phase 3 Stage 2)."""

import pytest
import numpy as np
from pathlib import Path

from outgraph.ml.geometry.ground_grid import (
    GroundGrid,
    GroundGridOutOfBoundsError,
)
from outgraph.ml.geometry.grid_projection import (
    GridProjector,
    GridProjectionError,
)

OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"
TMC2_CSV_REL = "data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv"


@pytest.fixture(scope="module")
def real_projector():
    """Provides initialized GridProjector with real OHRC and TMC-2 GroundGrids."""
    g_ohr = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    g_tmc = GroundGrid.from_csv(TMC2_CSV_REL, use_cache=True)
    return GridProjector(source_grid=g_ohr, target_grid=g_tmc)


@pytest.fixture
def synthetic_overlapping_projector():
    """Constructs two synthetic rectilinear GroundGrids with known 100% overlap."""
    # Sensor 1 (Source, High-Res: 100x100 pixels, covering lon 20-21, lat 0-1)
    p1 = np.repeat(np.linspace(0, 99, 10), 10).astype(np.int32)
    s1 = np.tile(np.linspace(0, 99, 10), 10).astype(np.int32)
    # lon linearly increases with pixel, lat linearly increases with scan
    lon1 = 20.0 + (p1 / 99.0) * 1.0
    lat1 = 0.0 + (s1 / 99.0) * 1.0

    # Sensor 2 (Target, Low-Res: 20x20 pixels, covering lon 19.5-21.5, lat -0.5 to 1.5)
    p2 = np.repeat(np.linspace(0, 19, 5), 5).astype(np.int32)
    s2 = np.tile(np.linspace(0, 19, 5), 5).astype(np.int32)
    lon2 = 19.5 + (p2 / 19.0) * 2.0
    lat2 = -0.5 + (s2 / 19.0) * 2.0

    grid_src = GroundGrid(
        source_path="mock_source",
        pixels=p1,
        scans=s1,
        lons=lon1,
        lats=lat1,
        is_rectilinear=True,
    )
    grid_tgt = GroundGrid(
        source_path="mock_target",
        pixels=p2,
        scans=s2,
        lons=lon2,
        lats=lat2,
        is_rectilinear=True,
    )
    return GridProjector(source_grid=grid_src, target_grid=grid_tgt)


def test_grid_projector_initialization_type_safety():
    """Verifies that GridProjector rejects invalid grid types."""
    with pytest.raises(TypeError, match="must be instances of GroundGrid"):
        GridProjector("invalid", "invalid")  # type: ignore


def test_grid_projector_synthetic_exact_projection(synthetic_overlapping_projector):
    """Verifies exact reference-datum projection and sub-pixel round trip on known overlap."""
    proj = synthetic_overlapping_projector

    # Source pixel (50, 50) -> lon 20.505, lat 0.505 -> Target pixel should be around ~9.5, 9.5
    src_p, src_s = 49.5, 49.5
    tgt_p, tgt_s = proj.project_source_to_target(src_p, src_s)

    assert np.isfinite(tgt_p)
    assert np.isfinite(tgt_s)

    # Round trip: target -> source
    rec_p, rec_s = proj.project_target_to_source(tgt_p, tgt_s)
    assert rec_p == pytest.approx(src_p, abs=1e-3)
    assert rec_s == pytest.approx(src_s, abs=1e-3)


def test_grid_projector_real_ohrc_vertices(real_projector):
    """Tests projection of real OHRC corners to TMC-2 pixel space.

    Physical geometry expectation:
    OHRC Western corners (pixel 0.0) fall outside TMC-2's Delaunay convex hull.
    OHRC Eastern corners (pixel 11999.0) lie on the Western boundary of TMC-2's hull.
    """
    proj = real_projector

    # 1. Top-Left / Western corner: (0, 0)
    p_tl, s_tl = proj.project_ohrc_to_tmc2(0.0, 0.0)
    assert np.isnan(p_tl) and np.isnan(s_tl)

    # 2. Bottom-Left / Western corner: (0, 78174)
    p_bl, s_bl = proj.project_ohrc_to_tmc2(0.0, 78174.0)
    assert np.isnan(p_bl) and np.isnan(s_bl)

    # 3. Top-Right / Eastern corner: (11999, 0)
    p_tr, s_tr = proj.project_ohrc_to_tmc2(11999.0, 0.0)
    assert np.isfinite(p_tr) and np.isfinite(s_tr)
    assert p_tr == pytest.approx(0.0, abs=1e-2)
    assert 58000.0 < s_tr < 61000.0

    # 4. Bottom-Right / Eastern corner: (11999, 78174)
    p_br, s_br = proj.project_ohrc_to_tmc2(11999.0, 78174.0)
    assert np.isfinite(p_br) and np.isfinite(s_br)
    assert p_br == pytest.approx(0.0, abs=1e-2)
    assert 63000.0 < s_br < 66000.0


def test_grid_projector_random_interior_points(real_projector):
    """Tests projection across multiple interior OHRC coordinates."""
    proj = real_projector
    rng = np.random.RandomState(42)

    # Sample 50 points on the eastern half (pixel > 8000)
    test_p = rng.uniform(8000.0, 11990.0, 50)
    test_s = rng.uniform(100.0, 78000.0, 50)

    tgt_p, tgt_s = proj.project_ohrc_to_tmc2(test_p, test_s)

    assert len(tgt_p) == 50
    assert len(tgt_s) == 50

    # Points on the far east fall within the TMC-2 triangulation
    valid = np.isfinite(tgt_p) & np.isfinite(tgt_s)
    assert np.sum(valid) > 0

    # Valid predicted scans must fall within TMC-2 scan domain
    assert np.all(tgt_s[valid] >= proj.target_grid.scan_min)
    assert np.all(tgt_s[valid] <= proj.target_grid.scan_max)


def test_grid_projector_vectorized_shapes(real_projector):
    """Verifies that vectorization preserves input array dimensions (1D and 2D)."""
    proj = real_projector

    # 1D array
    p_1d = np.array([1000.0, 11000.0, 11900.0])
    s_1d = np.array([5000.0, 40000.0, 70000.0])
    out_p_1d, out_s_1d = proj.project_ohrc_to_tmc2(p_1d, s_1d)

    assert out_p_1d.shape == (3,)
    assert out_s_1d.shape == (3,)

    # 2D array
    p_2d = np.array([[1000.0, 11000.0], [5000.0, 11900.0]])
    s_2d = np.array([[5000.0, 40000.0], [20000.0, 70000.0]])
    out_p_2d, out_s_2d = proj.project_ohrc_to_tmc2(p_2d, s_2d)

    assert out_p_2d.shape == (2, 2)
    assert out_s_2d.shape == (2, 2)


def test_grid_projector_out_of_bounds_handling(real_projector):
    """Verifies out-of-bounds rejection via NaN return and explicit exception raising."""
    proj = real_projector

    # 1. Negative OHRC coordinates
    p_nan, s_nan = proj.project_ohrc_to_tmc2(-10.0, 500.0, raise_out_of_bounds=False)
    assert np.isnan(p_nan) and np.isnan(s_nan)

    # 2. Raise exception on negative coordinates
    with pytest.raises(GroundGridOutOfBoundsError):
        proj.project_ohrc_to_tmc2(-10.0, 500.0, raise_out_of_bounds=True)

    # 3. Raise exception when OHRC coordinate is outside TMC-2 footprint
    with pytest.raises(GroundGridOutOfBoundsError):
        proj.project_ohrc_to_tmc2(0.0, 0.0, raise_out_of_bounds=True)


def test_grid_projector_domain_check_methods(real_projector):
    """Verifies is_source_in_target_domain and is_ground_in_target_domain."""
    proj = real_projector

    # Real point inside TMC-2 interior
    lon_tmc_inside = 24.0
    lat_tmc_inside = 0.5
    assert proj.is_ground_in_target_domain(lon_tmc_inside, lat_tmc_inside) is True

    # Real point far outside TMC-2
    assert proj.is_ground_in_target_domain(0.0, 0.0) is False

    # OHRC pixel 0 is outside TMC-2 domain
    assert proj.is_source_in_target_domain(0.0, 0.0) is False

    # Vectorized domain check
    p_vec = np.array([0.0, 11999.0])
    s_vec = np.array([0.0, 50000.0])
    in_domain = proj.is_source_in_target_domain(p_vec, s_vec)
    assert in_domain.shape == (2,)
    assert in_domain[0] is False or in_domain[0] == 0


def test_grid_projector_geographic_overlap(real_projector):
    """Verifies get_geographic_overlap reporting bounding box intersection."""
    proj = real_projector
    overlap = proj.get_geographic_overlap()

    assert overlap["bbox_intersection"]["has_overlap"] is True
    assert overlap["bbox_intersection"]["lon_min"] == pytest.approx(23.3720, abs=1e-3)
    assert overlap["bbox_intersection"]["lon_max"] == pytest.approx(23.4954, abs=1e-3)
    assert overlap["bbox_intersection"]["lat_min"] == pytest.approx(0.2247, abs=1e-3)
    assert overlap["bbox_intersection"]["lat_max"] == pytest.approx(1.0689, abs=1e-3)


def test_grid_projector_deterministic_repeatability(real_projector):
    """Verifies that projection results are strictly deterministic across repeated calls."""
    proj = real_projector
    p_test = np.array([10000.0, 11500.0])
    s_test = np.array([20000.0, 50000.0])

    p1, s1 = proj.project_ohrc_to_tmc2(p_test, s_test)
    p2, s2 = proj.project_ohrc_to_tmc2(p_test, s_test)

    np.testing.assert_array_equal(p1, p2)
    np.testing.assert_array_equal(s1, s2)


def test_grid_projector_round_trip_residuals(synthetic_overlapping_projector):
    """Verifies round-trip residual measurement on synthetic overlapping grid."""
    proj = synthetic_overlapping_projector

    p_test = np.array([20.0, 50.0, 80.0])
    s_test = np.array([20.0, 50.0, 80.0])

    res = proj.compute_round_trip_residuals(p_test, s_test)

    assert res["total_points"] == 3
    assert res["valid_count"] == 3
    assert res["invalid_count"] == 0
    assert res["statistics"]["max_ground_residual_m"] < 1.0  # Sub-meter consistency


def test_grid_projector_tmc2_inverse_recovery_across_sensor_width(real_projector):
    """Verifies that the TMC-2 inverse interpolator accurately recovers all pixel columns (0 to 3999).
    
    Proves that the TMC-2 inverse engine is healthy and that TMC pixel=0 in OHRC projection
    is not an interpolator defect.
    """
    g_tmc = real_projector.target_grid
    sample_pixels = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500, 3999]
    
    for p in sample_pixels:
        mask = (g_tmc._raw_pixels == p) & (g_tmc._raw_lats >= 0.22) & (g_tmc._raw_lats <= 1.07)
        idx = np.where(mask)[0][0]
        lon = float(g_tmc._raw_lons[idx])
        lat = float(g_tmc._raw_lats[idx])
        orig_s = float(g_tmc._raw_scans[idx])

        rec_p, rec_s = g_tmc.ground_to_pixel(lon, lat)
        assert abs(rec_p - p) < 1e-4, f"Failed recovery for pixel {p}: got {rec_p}"
        assert abs(rec_s - orig_s) < 1e-4, f"Failed recovery for scan {orig_s}: got {rec_s}"


def test_grid_projector_real_ohrc_western_boundary_collapse(real_projector):
    """Regression test documenting real OHRC->TMC-2 projection behavior.
    
    Due to the physical ~1.4 km gap separating the OHRC product strip from the
    TMC-2 swath, all points in OHRC lie to the west of TMC-2's western boundary (pixel 0).
    The 2D Delaunay convex hull of the curved TMC-2 strip spans this concave bay with
    boundary triangles whose vertices all have pixel=0. Consequently, all finite real
    projections collapse strictly to TMC-2 pixel=0.0.
    """
    proj = real_projector
    g_ohr = proj.source_grid

    p_grid = np.linspace(g_ohr.pixel_min, g_ohr.pixel_max, 10)
    s_grid = np.linspace(g_ohr.scan_min, g_ohr.scan_max, 10)
    P, S = np.meshgrid(p_grid, s_grid)

    tgt_p, tgt_s = proj.project_ohrc_to_tmc2(P.ravel(), S.ravel())
    valid = np.isfinite(tgt_p) & np.isfinite(tgt_s)

    # Valid points exist along the eastern half of the OHRC image
    assert np.sum(valid) > 0

    # Every single valid projected point must evaluate to TMC-2 pixel 0.0 (western edge)
    np.testing.assert_allclose(tgt_p[valid], 0.0, atol=1e-3)

    # Scans must fall smoothly within the active line range matching OHRC latitudes
    assert np.all(tgt_s[valid] >= 59000.0)
    assert np.all(tgt_s[valid] <= 65000.0)

