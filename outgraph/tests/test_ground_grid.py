"""Unit and Integration Tests for Ground-Grid Georeferencing Engine (Phase 3 Stage 1)."""

import pytest
import numpy as np
from pathlib import Path

from outgraph.ml.geometry.ground_grid import (
    GroundGrid,
    GroundGridValidationError,
    GroundGridOutOfBoundsError,
)

OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"
TMC2_CSV_REL = "data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv"


def test_ground_grid_ohrc_loading_and_structure():
    """Verifies OHRC ground grid loading, record count, and rectilinear lattice structure."""
    grid = GroundGrid.from_csv(OHRC_CSV_REL)

    assert grid.num_records == 94743
    assert grid.is_rectilinear is True
    assert len(grid.unique_pixels) == 121
    assert len(grid.unique_scans) == 783

    assert grid.pixel_min == 0.0
    assert grid.pixel_max == 11999.0
    assert grid.scan_min == 0.0
    assert grid.scan_max == 78174.0

    assert grid.lon_min == pytest.approx(23.3720, abs=1e-3)
    assert grid.lon_max == pytest.approx(23.4954, abs=1e-3)
    assert grid.lat_min == pytest.approx(0.2247, abs=1e-3)
    assert grid.lat_max == pytest.approx(1.0689, abs=1e-3)


def test_ground_grid_tmc2_loading_and_structure():
    """Verifies TMC-2 ground grid loading, record count, and rectilinear lattice structure."""
    grid = GroundGrid.from_csv(TMC2_CSV_REL)

    assert grid.num_records == 88027
    assert grid.is_rectilinear is True
    assert len(grid.unique_pixels) == 41
    assert len(grid.unique_scans) == 2147

    assert grid.pixel_min == 0.0
    assert grid.pixel_max == 3999.0
    assert grid.scan_min == 0.0
    assert grid.scan_max == 214556.0

    assert grid.lon_min == pytest.approx(22.5413, abs=1e-3)
    assert grid.lon_max == pytest.approx(24.7212, abs=1e-3)
    assert grid.lat_min == pytest.approx(-23.8893, abs=1e-3)
    assert grid.lat_max == pytest.approx(10.6250, abs=1e-3)


def test_ground_grid_exact_vertices_round_trip():
    """Verifies that calibrated grid vertices produce zero interpolation error on round trip."""
    grid_ohr = GroundGrid.from_csv(OHRC_CSV_REL)

    test_pixels = [0.0, 100.0, 500.0, 1000.0, 6000.0, 11900.0, 11999.0]
    test_scans = [0.0, 100.0, 500.0, 1000.0, 40000.0, 78100.0, 78174.0]

    for p, s in zip(test_pixels, test_scans):
        lon, lat = grid_ohr.pixel_to_ground(p, s)
        p_rec, s_rec = grid_ohr.ground_to_pixel(lon, lat)

        assert abs(p_rec - p) < 1e-3, f"Pixel error too high at ({p}, {s}): {abs(p_rec - p)}"
        assert abs(s_rec - s) < 1e-3, f"Scan error too high at ({p}, {s}): {abs(s_rec - s)}"


def test_ground_grid_continuous_interior_round_trip():
    """Measures empirical round-trip interpolation accuracy on interior non-vertex coordinates."""
    grid_ohr = GroundGrid.from_csv(OHRC_CSV_REL)
    grid_tmc = GroundGrid.from_csv(TMC2_CSV_REL)

    rng = np.random.RandomState(42)

    # 1. OHRC interior test (50 random points)
    ohr_p = rng.uniform(10.0, 11980.0, 50)
    ohr_s = rng.uniform(10.0, 78160.0, 50)

    lons, lats = grid_ohr.pixel_to_ground(ohr_p, ohr_s)
    p_rec, s_rec = grid_ohr.ground_to_pixel(lons, lats)

    err_p = np.abs(ohr_p - p_rec)
    err_s = np.abs(ohr_s - s_rec)

    # Median error must be sub-pixel (empirically < 0.001 px)
    assert np.median(err_p) < 0.01
    assert np.median(err_s) < 0.01
    assert np.max(err_p) < 0.05
    assert np.max(err_s) < 0.05

    # 2. TMC-2 interior test (50 random points)
    tmc_p = rng.uniform(10.0, 3980.0, 50)
    tmc_s = rng.uniform(100.0, 214000.0, 50)

    lons_t, lats_t = grid_tmc.pixel_to_ground(tmc_p, tmc_s)
    pt_rec, st_rec = grid_tmc.ground_to_pixel(lons_t, lats_t)

    err_pt = np.abs(tmc_p - pt_rec)
    err_st = np.abs(tmc_s - st_rec)

    assert np.median(err_pt) < 0.01
    assert np.median(err_st) < 0.01
    assert np.max(err_pt) < 0.05
    assert np.max(err_st) < 0.05


def test_ground_grid_boundaries():
    """Verifies domain boundary handling on extreme corners."""
    grid = GroundGrid.from_csv(OHRC_CSV_REL)

    corners = [
        (grid.pixel_min, grid.scan_min),
        (grid.pixel_max, grid.scan_min),
        (grid.pixel_min, grid.scan_max),
        (grid.pixel_max, grid.scan_max),
    ]

    for p, s in corners:
        assert grid.contains_pixel(p, s) is True
        lon, lat = grid.pixel_to_ground(p, s)
        assert np.isfinite(lon)
        assert np.isfinite(lat)
        assert grid.contains_ground(lon, lat) is True


def test_ground_grid_outside_domain_rejection():
    """Verifies that queries outside the calibrated grid domain are rejected cleanly."""
    grid = GroundGrid.from_csv(OHRC_CSV_REL)

    # 1. Pixel out of bounds -> returns NaN
    lon_nan, lat_nan = grid.pixel_to_ground(-1.0, 100.0)
    assert np.isnan(lon_nan) and np.isnan(lat_nan)

    lon_nan2, lat_nan2 = grid.pixel_to_ground(100.0, 80000.0)
    assert np.isnan(lon_nan2) and np.isnan(lat_nan2)

    # 2. Pixel out of bounds with raise_out_of_bounds=True -> raises exception
    with pytest.raises(GroundGridOutOfBoundsError):
        grid.pixel_to_ground(-5.0, 100.0, raise_out_of_bounds=True)

    with pytest.raises(GroundGridOutOfBoundsError):
        grid.pixel_to_ground(100.0, 90000.0, raise_out_of_bounds=True)

    # 3. Ground out of bounds -> returns NaN
    p_nan, s_nan = grid.ground_to_pixel(0.0, 0.0)
    assert np.isnan(p_nan) and np.isnan(s_nan)

    # 4. Ground out of bounds with raise_out_of_bounds=True -> raises exception
    with pytest.raises(GroundGridOutOfBoundsError):
        grid.ground_to_pixel(0.0, 0.0, raise_out_of_bounds=True)

    # 5. contains_pixel and contains_ground return False
    assert grid.contains_pixel(-10.0, 50.0) is False
    assert grid.contains_pixel(50.0, 100000.0) is False
    assert grid.contains_ground(0.0, 0.0) is False
    assert grid.contains_ground(180.0, 85.0) is False


def test_ground_grid_vectorized_and_shape_preservation():
    """Verifies vectorized queries across multiple dimensions."""
    grid = GroundGrid.from_csv(OHRC_CSV_REL)

    # 1D array
    p_1d = np.array([100.0, 200.0, 300.0])
    s_1d = np.array([500.0, 600.0, 700.0])
    lons_1d, lats_1d = grid.pixel_to_ground(p_1d, s_1d)
    assert lons_1d.shape == (3,)
    assert lats_1d.shape == (3,)

    # 2D array
    p_2d = np.array([[100.0, 200.0], [300.0, 400.0]])
    s_2d = np.array([[500.0, 600.0], [700.0, 800.0]])
    lons_2d, lats_2d = grid.pixel_to_ground(p_2d, s_2d)
    assert lons_2d.shape == (2, 2)
    assert lats_2d.shape == (2, 2)

    p_rec, s_rec = grid.ground_to_pixel(lons_2d, lats_2d)
    assert p_rec.shape == (2, 2)
    assert s_rec.shape == (2, 2)
    np.testing.assert_allclose(p_rec, p_2d, atol=0.01)
    np.testing.assert_allclose(s_rec, s_2d, atol=0.01)


def test_ground_grid_validation_failures(tmp_path):
    """Verifies that malformed or incomplete CSV files trigger validation errors."""
    # 1. Missing columns
    bad_csv1 = tmp_path / "bad_cols.csv"
    bad_csv1.write_text("Longitude,Latitude,Pixel\n23.4,0.5,100\n", encoding="utf-8")
    with pytest.raises(GroundGridValidationError, match="Missing required column 'scan'"):
        GroundGrid.from_csv(bad_csv1, use_cache=False)

    # 2. Empty file
    bad_csv2 = tmp_path / "empty.csv"
    bad_csv2.write_text("", encoding="utf-8")
    with pytest.raises(GroundGridValidationError, match="Empty CSV file"):
        GroundGrid.from_csv(bad_csv2, use_cache=False)

    # 3. Malformed numeric values
    bad_csv3 = tmp_path / "bad_num.csv"
    bad_csv3.write_text("Longitude,Latitude,Pixel,Scan\nINVALID,0.5,100,200\n", encoding="utf-8")
    with pytest.raises(GroundGridValidationError, match="Malformed numeric data"):
        GroundGrid.from_csv(bad_csv3, use_cache=False)

    # 4. Duplicate coordinates
    bad_csv4 = tmp_path / "duplicates.csv"
    bad_csv4.write_text(
        "Longitude,Latitude,Pixel,Scan\n"
        "23.4,0.5,100,200\n"
        "23.5,0.6,100,200\n"
        "23.6,0.7,200,200\n"
        "23.7,0.8,200,300\n",
        encoding="utf-8",
    )
    with pytest.raises(GroundGridValidationError, match="Duplicate"):
        GroundGrid.from_csv(bad_csv4, use_cache=False)


def test_ground_grid_caching():
    """Verifies that from_csv caches instance by resolved path."""
    g1 = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    g2 = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    assert g1 is g2
