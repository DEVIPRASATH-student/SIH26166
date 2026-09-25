"""Unit and Integration Tests for Elevation-Dependent Parallax Model (Stage 3.3)."""

import pytest
import numpy as np

from outgraph.ml.geometry.parallax_model import (
    ParallaxModel,
    OHRC_PARALLAX_PARAMS,
    TMC2_PARALLAX_PARAMS,
    SensorParallaxParams,
)


@pytest.fixture
def ohrc_parallax():
    return ParallaxModel(OHRC_PARALLAX_PARAMS)


@pytest.fixture
def tmc2_parallax():
    return ParallaxModel(TMC2_PARALLAX_PARAMS)


def test_parallax_zero_elevation_gives_zero_displacement(ohrc_parallax, tmc2_parallax):
    """Verifies that h = 0 produces zero terrain displacement regardless of pixel position."""
    for model in [ohrc_parallax, tmc2_parallax]:
        for sample in [0.0, 500.0, model.params.center_sample, model.params.total_samples - 1]:
            disp = model.compute_ground_displacement(elevation_m=0.0, pixel_sample=sample)
            assert disp["displacement_magnitude_m"] == pytest.approx(0.0, abs=1e-6)
            assert disp["cross_track_displacement_m"] == pytest.approx(0.0, abs=1e-6)

            dp = model.compute_pixel_displacement(elevation_m=0.0, pixel_sample=sample)
            assert dp == pytest.approx(0.0, abs=1e-6)


def test_parallax_nadir_center_gives_zero_displacement(ohrc_parallax, tmc2_parallax):
    """Verifies that the camera nadir center has zero look angle and zero relief displacement."""
    for model in [ohrc_parallax, tmc2_parallax]:
        center = model.params.center_sample
        for elev in [-3000.0, -1000.0, 1000.0, 3000.0]:
            disp = model.compute_ground_displacement(elevation_m=elev, pixel_sample=center)
            assert disp["displacement_magnitude_m"] == pytest.approx(0.0, abs=1e-6)
            assert disp["look_angle_deg"] == pytest.approx(0.0, abs=1e-6)


def test_parallax_physical_directionality(tmc2_parallax):
    """Verifies that elevation signs produce physically consistent displacement directions."""
    model = tmc2_parallax
    # Sample on Eastern wing (sample > center)
    sample_east = 3500.0
    assert sample_east > model.params.center_sample

    # 1. Depression (h = -2000m, e.g. lunar mare) should displace outward (positive cross-track)
    disp_dep = model.compute_ground_displacement(elevation_m=-2000.0, pixel_sample=sample_east)
    assert disp_dep["cross_track_displacement_m"] > 0.0

    # 2. Elevated feature (h = +2000m, e.g. crater rim) should displace inward (negative cross-track)
    disp_elev = model.compute_ground_displacement(elevation_m=2000.0, pixel_sample=sample_east)
    assert disp_elev["cross_track_displacement_m"] < 0.0

    # Magnitudes must be equal for symmetric elevation
    assert disp_dep["displacement_magnitude_m"] == pytest.approx(disp_elev["displacement_magnitude_m"], rel=1e-4)


def test_parallax_vectorized_and_shape_preservation(tmc2_parallax):
    """Verifies that ParallaxModel preserves 1D and 2D input array dimensions."""
    model = tmc2_parallax

    # 1D array
    h_1d = np.array([-2000.0, -1500.0, 500.0])
    p_1d = np.array([500.0, model.params.center_sample, 3500.0])
    dp_1d = model.compute_pixel_displacement(h_1d, p_1d)

    assert isinstance(dp_1d, np.ndarray)
    assert dp_1d.shape == (3,)
    assert np.all(np.isfinite(dp_1d))

    # Center sample must have zero displacement
    assert dp_1d[1] == pytest.approx(0.0, abs=1e-6)


    # 2D array
    h_2d = np.array([[-2000.0, -1000.0], [0.0, 1000.0]])
    p_2d = np.array([[500.0, 1000.0], [2000.0, 3000.0]])
    dp_2d = model.compute_pixel_displacement(h_2d, p_2d)

    assert isinstance(dp_2d, np.ndarray)
    assert dp_2d.shape == (2, 2)
    assert np.all(np.isfinite(dp_2d))


def test_parallax_deterministic_repeatability(ohrc_parallax):
    """Verifies bitwise repeatability of parallax computations."""
    disp1 = ohrc_parallax.compute_ground_displacement(-1890.0, 10000.0)
    disp2 = ohrc_parallax.compute_ground_displacement(-1890.0, 10000.0)

    assert disp1["cross_track_displacement_m"] == disp2["cross_track_displacement_m"]
    assert disp1["look_angle_deg"] == disp2["look_angle_deg"]


def test_parallax_out_of_bounds_and_nan(ohrc_parallax):
    """Verifies that non-finite inputs propagate cleanly as NaN."""
    disp = ohrc_parallax.compute_ground_displacement(np.nan, 5000.0)
    assert np.isnan(disp["cross_track_displacement_m"])


def test_parallax_max_displacement_bounds(ohrc_parallax, tmc2_parallax):
    """Verifies theoretical maximum displacement boundaries on OHRC and TMC-2.

    Demonstrates that for realistic elevations (|h| <= 2500m):
    Max displacement is <= 300 meters, which CANNOT bridge the 1.5 - 2.1 km physical gap.
    """
    ohrc_max = ohrc_parallax.get_max_possible_displacement(max_elevation_abs_m=2500.0)
    tmc2_max = tmc2_parallax.get_max_possible_displacement(max_elevation_abs_m=2500.0)

    # OHRC narrow FOV (swath ~3 km wide at 102 km altitude)
    assert ohrc_max["max_look_angle_deg"] < 1.5  # ~0.84 deg
    assert ohrc_max["max_ground_displacement_m"] < 50.0  # < 50m displacement

    # TMC-2 wider swath (~24 km wide at 121 km altitude)
    assert tmc2_max["max_look_angle_deg"] < 7.0  # ~5.6 deg
    assert tmc2_max["max_ground_displacement_m"] < 300.0  # ~246m displacement

    # Crucial scientific comparison:
    # 246m << 1491m (minimum footprint gap)
    assert tmc2_max["max_ground_displacement_m"] < 1491.0
