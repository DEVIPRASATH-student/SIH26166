"""Unit and Integration Tests for Real Lunar DEM Interface (Stage 3.1)."""

import pytest
import numpy as np
from pathlib import Path

from outgraph.ml.geometry.ground_grid import GroundGrid
from outgraph.ml.geometry.dem_interface import (
    DEMInterface,
    DEMError,
    DEMOutOfBoundsError,
)

OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"


@pytest.fixture(scope="module")
def dem():
    """Provides loaded DEMInterface on real SLDEM2015 dataset."""
    return DEMInterface.load_default(use_cache=True)


@pytest.fixture(scope="module")
def ohrc_grid():
    """Provides loaded GroundGrid for OHRC."""
    return GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)


def test_dem_metadata_validity(dem):
    """Verifies that DEM metadata matches official PDS SLDEM2015 specifications."""
    meta = dem.get_metadata()

    assert meta["source_name"] == "SLDEM2015_512_00N_30N_000_045"
    assert meta["resolution_ppd"] == 512.0
    assert meta["reference_radius_km"] == 1737.4
    assert meta["nodata_value"] == -32768.0
    assert meta["elevation_units"] == "meters"
    assert "Simple Cylindrical" in meta["crs"]
    assert meta["spatial_resolution_m"] == pytest.approx(59.225, abs=0.1)


def test_dem_coverage_and_buffering(dem, ohrc_grid):
    """Verifies that the buffered DEM completely encloses the OHRC ground footprint."""
    # OHRC Footprint
    assert ohrc_grid.lon_min >= dem.lon_min
    assert ohrc_grid.lon_max <= dem.lon_max
    assert ohrc_grid.lat_min >= dem.lat_min
    assert ohrc_grid.lat_max <= dem.lat_max

    # Buffer margin check: buffer should be >= 0.2 deg on all sides
    assert (ohrc_grid.lon_min - dem.lon_min) >= 0.2
    assert (dem.lon_max - ohrc_grid.lon_max) >= 0.2
    assert (ohrc_grid.lat_min - dem.lat_min) >= 0.2
    assert (dem.lat_max - ohrc_grid.lat_max) >= 0.2


def test_dem_deterministic_sampling(dem):
    """Verifies that elevation sampling is bitwise deterministic across calls."""
    lon, lat = 23.45, 0.65
    val1 = dem.sample(lon, lat, method="bilinear")
    val2 = dem.sample(lon, lat, method="bilinear")

    assert isinstance(val1, float)
    assert val1 == val2
    assert np.isfinite(val1)


def test_dem_ohrc_corners_and_center_sampling(dem, ohrc_grid):
    """Samples elevations at the four corners and center of OHRC footprint."""
    corners = [
        (ohrc_grid.pixel_min, ohrc_grid.scan_min),
        (ohrc_grid.pixel_max, ohrc_grid.scan_min),
        (ohrc_grid.pixel_min, ohrc_grid.scan_max),
        (ohrc_grid.pixel_max, ohrc_grid.scan_max),
        ((ohrc_grid.pixel_min + ohrc_grid.pixel_max) / 2, (ohrc_grid.scan_min + ohrc_grid.scan_max) / 2),
    ]

    for p, s in corners:
        lon, lat = ohrc_grid.pixel_to_ground(p, s)
        elev = dem.sample(lon, lat)

        assert np.isfinite(elev)
        # In this lunar equatorial region (near Sinus Medii / Mare Tranquillitatis),
        # elevation is known to lie between -2500m and -1500m relative to 1737.4 km
        assert -2600.0 < elev < -1400.0


def test_dem_20_distributed_ohrc_points_statistics(dem, ohrc_grid):
    """Computes comprehensive elevation statistics across 20 distributed OHRC points."""
    pixels = np.linspace(ohrc_grid.pixel_min, ohrc_grid.pixel_max, 4)
    scans = np.linspace(ohrc_grid.scan_min, ohrc_grid.scan_max, 5)
    P, S = np.meshgrid(pixels, scans)

    lons, lats = ohrc_grid.pixel_to_ground(P.ravel(), S.ravel())
    stats = dem.sample_statistics(lons, lats)

    assert stats["total_points"] == 20
    assert stats["valid_count"] == 20
    assert stats["nodata_count"] == 0
    assert stats["valid_percentage"] == 100.0
    assert stats["nodata_percentage"] == 0.0

    assert -2600.0 < stats["min_elevation_m"] < -1700.0
    assert -2100.0 < stats["max_elevation_m"] < -1400.0
    assert stats["min_elevation_m"] <= stats["mean_elevation_m"] <= stats["max_elevation_m"]
    assert stats["std_elevation_m"] > 0.0


def test_dem_vectorized_and_shape_preservation(dem):
    """Verifies that DEM sampling preserves 1D and 2D input array shapes."""
    # 1D array
    lons_1d = np.array([23.38, 23.42, 23.48])
    lats_1d = np.array([0.30, 0.60, 0.90])
    out_1d = dem.sample(lons_1d, lats_1d)

    assert isinstance(out_1d, np.ndarray)
    assert out_1d.shape == (3,)
    assert np.all(np.isfinite(out_1d))

    # 2D array
    lons_2d = np.array([[23.38, 23.42], [23.44, 23.48]])
    lats_2d = np.array([[0.30, 0.40], [0.60, 0.90]])
    out_2d = dem.sample(lons_2d, lats_2d)

    assert isinstance(out_2d, np.ndarray)
    assert out_2d.shape == (2, 2)
    assert np.all(np.isfinite(out_2d))


def test_dem_out_of_bounds_rejection(dem):
    """Verifies clean out-of-bounds rejection via NaN and exception."""
    # Point outside DEM footprint (e.g. lon=10.0, lat=40.0)
    assert dem.contains_coordinate(10.0, 40.0) is False

    val_nan = dem.sample(10.0, 40.0, raise_out_of_bounds=False)
    assert np.isnan(val_nan)

    with pytest.raises(DEMOutOfBoundsError):
        dem.sample(10.0, 40.0, raise_out_of_bounds=True)


def test_dem_synthetic_instance():
    """Verifies that DEMInterface works with custom mock elevation arrays."""
    mock_elev = np.array([[100.0, 200.0], [300.0, 400.0]], dtype=np.float32)
    custom_dem = DEMInterface(
        elevation_grid=mock_elev,
        lat_min=0.0,
        lat_max=1.0,
        lon_min=20.0,
        lon_max=21.0,
        resolution_ppd=1.0,
    )
    # Center sample: lon 20.5, lat 0.5 -> should be exactly 250.0 m
    val = custom_dem.sample(20.5, 0.5, method="bilinear")
    assert val == pytest.approx(250.0, abs=1e-3)
