"""Unit and Integration Tests for DEM-Aware Terrain Geometry (Stage 3.2)."""

import pytest
import numpy as np

from outgraph.ml.geometry.ground_grid import GroundGrid
from outgraph.ml.geometry.dem_interface import DEMInterface
from outgraph.ml.geometry.terrain_geometry import TerrainGeometry

OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"


@pytest.fixture(scope="module")
def terrain_geo():
    """Provides initialized TerrainGeometry on real OHRC GroundGrid and SLDEM2015."""
    g_ohr = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    dem = DEMInterface.load_default(use_cache=True)
    return TerrainGeometry(ground_grid=g_ohr, dem=dem)


def test_terrain_geometry_type_safety():
    """Verifies that TerrainGeometry rejects invalid input types."""
    with pytest.raises(TypeError, match="must be an instance of GroundGrid"):
        TerrainGeometry("invalid", "invalid")  # type: ignore


def test_terrain_geometry_reference_datum_equivalence(terrain_geo):
    """Verifies that use_dem=False exactly reproduces Stage 2 reference-datum coordinates (h=0)."""
    p, s = 6000.0, 39000.0

    # 1. Direct GroundGrid call (Stage 2)
    lon_ref, lat_ref = terrain_geo.ground_grid.pixel_to_ground(p, s)

    # 2. TerrainGeometry with use_dem=False
    lon_geo, lat_geo, h_geo = terrain_geo.pixel_to_terrain(p, s, use_dem=False, default_elevation=0.0)

    assert lon_geo == lon_ref
    assert lat_geo == lat_ref
    assert h_geo == 0.0


def test_terrain_geometry_real_dem_elevation_insertion(terrain_geo):
    """Verifies that real DEM elevation is sampled without modifying the underlying GroundGrid."""
    p, s = 6000.0, 39000.0

    lon_ref, lat_ref = terrain_geo.ground_grid.pixel_to_ground(p, s)
    lon_geo, lat_geo, h_geo = terrain_geo.pixel_to_terrain(p, s, use_dem=True)

    # Longitude and latitude must match exactly
    assert lon_geo == lon_ref
    assert lat_geo == lat_ref

    # Elevation must reflect real lunar topography (-2500m to -1500m)
    assert np.isfinite(h_geo)
    assert -2500.0 < h_geo < -1500.0

    # Underlying GroundGrid must remain unchanged
    assert terrain_geo.ground_grid.pixel_min == 0.0
    assert terrain_geo.ground_grid.pixel_max == 11999.0


def test_terrain_geometry_deterministic_sampling(terrain_geo):
    """Verifies that 3D coordinate generation is bitwise deterministic."""
    p, s = 8500.0, 42000.0
    res1 = terrain_geo.pixel_to_terrain(p, s, use_dem=True)
    res2 = terrain_geo.pixel_to_terrain(p, s, use_dem=True)

    assert res1[0] == res2[0]
    assert res1[1] == res2[1]
    assert res1[2] == res2[2]


def test_terrain_geometry_vectorized_and_shape_preservation(terrain_geo):
    """Verifies that vectorized calls preserve input array shapes across 1D and 2D."""
    # 1D array
    p_1d = np.array([1000.0, 6000.0, 11000.0])
    s_1d = np.array([10000.0, 40000.0, 70000.0])
    lons_1d, lats_1d, h_1d = terrain_geo.pixel_to_terrain(p_1d, s_1d, use_dem=True)

    assert lons_1d.shape == (3,)
    assert lats_1d.shape == (3,)
    assert h_1d.shape == (3,)
    assert np.all(np.isfinite(h_1d))

    # 2D array
    p_2d = np.array([[1000.0, 6000.0], [3000.0, 11000.0]])
    s_2d = np.array([[10000.0, 40000.0], [20000.0, 70000.0]])
    lons_2d, lats_2d, h_2d = terrain_geo.pixel_to_terrain(p_2d, s_2d, use_dem=True)

    assert lons_2d.shape == (2, 2)
    assert lats_2d.shape == (2, 2)
    assert h_2d.shape == (2, 2)
    assert np.all(np.isfinite(h_2d))


def test_terrain_geometry_out_of_bounds_propagation(terrain_geo):
    """Verifies that coordinates outside the GroundGrid domain propagate cleanly as NaN."""
    # Negative pixel
    lon_nan, lat_nan, h_nan = terrain_geo.pixel_to_terrain(-10.0, 500.0, use_dem=True)
    assert np.isnan(lon_nan)
    assert np.isnan(lat_nan)
    assert np.isnan(h_nan)


def test_terrain_geometry_transect(terrain_geo):
    """Verifies linear transect sampling across the image plane."""
    transect = terrain_geo.sample_transect(
        start_pixel=100.0, start_scan=100.0,
        end_pixel=11000.0, end_scan=70000.0,
        num_points=25,
    )

    assert len(transect["pixels"]) == 25
    assert len(transect["longitudes"]) == 25
    assert len(transect["terrain_elevations_m"]) == 25
    assert np.all(np.isfinite(transect["terrain_elevations_m"]))
    assert np.all(transect["datum_elevations_m"] == 0.0)
