"""Phase 6.1 Adversarial Red-Team Tests: Hostile Geometric & Datum Boundary Testing.

Evaluates the physical geometry pipeline against hostile boundary and datum conditions:
- Test Group A: Grounded Valid Boundaries (exact min/max pixel & scan for OHRC & TMC-2)
- Test Group B: Sub-Pixel Boundary Attack (epsilon inside, outside, half-pixel)
- Test Group C: Out-of-Bounds Attack (negatives, > max, NaN, +/-inf, astronomical finite)
- Test Group D: DEM Boundary Attack (exact bounds, out-of-domain, NaN, no-data)
- Test Group E: Target Swath Boundary (real OHRC/TMC-2 non-overlap and clamping defense)
- Test Group F: Datum Consistency Attack (swapped coordinates, extreme elevation offsets)
- Test Group G: Numerical Stability (microscopic deltas, mixed valid/NaN arrays, repeated queries)
"""

import pytest
import numpy as np
from pathlib import Path

from outgraph.ml.geometry.ground_grid import (
    GroundGrid,
    GroundGridOutOfBoundsError,
    GroundGridValidationError,
)
from outgraph.ml.geometry.dem_interface import (
    DEMInterface,
    DEMOutOfBoundsError,
)
from outgraph.ml.geometry.terrain_geometry import TerrainGeometry
from outgraph.ml.geometry.grid_projection import GridProjector
from outgraph.ml.geometry.parallax_model import (
    ParallaxModel,
    TMC2_PARALLAX_PARAMS,
    SensorParallaxParams,
)
from outgraph.ml.geometry.target_corridor import (
    TargetCorridorCalculator,
    CorridorResult,
)
from outgraph.ml.matchers.physical_matcher import (
    PhysicalCandidateEngine,
    PhysicalCandidate,
)

OHRC_CSV_REL = "data/real/ohrc/ch2_ohr_ncp_20210402T0546284043_d_img_d18/geometry/calibrated/20210402/ch2_ohr_ncp_20210402T0546284043_g_grd_d18.csv"
TMC2_CSV_REL = "data/real/tmc2/ch2_tmc_nca_20240523T1600309581_d_img_d18/geometry/calibrated/20240523/ch2_tmc_nca_20240523T1600309581_g_grd_d18.csv"


@pytest.fixture(scope="module")
def real_grids():
    """Loads calibrated OHRC and TMC-2 GroundGrid models."""
    g_ohr = GroundGrid.from_csv(OHRC_CSV_REL, use_cache=True)
    g_tmc = GroundGrid.from_csv(TMC2_CSV_REL, use_cache=True)
    return g_ohr, g_tmc


@pytest.fixture(scope="module")
def real_dem():
    """Loads default SLDEM2015 DEM interface."""
    return DEMInterface.load_default(use_cache=True)


@pytest.fixture(scope="module")
def real_physical_engine(real_grids, real_dem):
    """Initializes the PhysicalCandidateEngine on real datasets."""
    g_ohr, g_tmc = real_grids
    terrain_geo = TerrainGeometry(ground_grid=g_ohr, dem=real_dem)
    projector = GridProjector(source_grid=g_ohr, target_grid=g_tmc)
    corridor_calc = TargetCorridorCalculator(projector=projector, terrain_geo=terrain_geo)
    return PhysicalCandidateEngine(corridor_calc=corridor_calc)


# ==============================================================================
# TEST GROUP A: GROUNDED VALID BOUNDARIES
# ==============================================================================

class TestGroupA_GroundedValidBoundaries:
    """Verifies that exact boundary coordinates for calibrated GroundGrids remain valid."""

    def test_ohrc_exact_boundaries(self, real_grids):
        g_ohr, _ = real_grids
        # Calibrated discrete grid corners and integer boundary vertices
        exact_vertices = [
            (g_ohr.pixel_min, g_ohr.scan_min),
            (g_ohr.pixel_max, g_ohr.scan_min),
            (g_ohr.pixel_min, g_ohr.scan_max),
            (g_ohr.pixel_max, g_ohr.scan_max),
            (6000.0, g_ohr.scan_min),
            (6000.0, g_ohr.scan_max),
            (g_ohr.pixel_min, 40000.0),
            (g_ohr.pixel_max, 40000.0),
        ]

        for p, s in exact_vertices:
            assert g_ohr.contains_pixel(p, s) is True
            lon, lat = g_ohr.pixel_to_ground(p, s, raise_out_of_bounds=True)
            assert np.isfinite(lon) and np.isfinite(lat)
            assert g_ohr.lon_min <= lon <= g_ohr.lon_max
            assert g_ohr.lat_min <= lat <= g_ohr.lat_max

            # Round trip invertibility at exact calibrated grid vertices
            p_rt, s_rt = g_ohr.ground_to_pixel(lon, lat, raise_out_of_bounds=True)
            assert p_rt == pytest.approx(p, abs=0.5)
            assert s_rt == pytest.approx(s, abs=1.0)

        # Non-vertex sub-pixel midpoint on outer boundary (5999.5, scan_max)
        # Demonstrates Delaunay chord boundary behavior: points outside the linear
        # triangulation simplex safely return NaN rather than extrapolating.
        p_mid, s_mid = (5999.5, g_ohr.scan_max)
        assert g_ohr.contains_pixel(p_mid, s_mid) is True
        lon_m, lat_m = g_ohr.pixel_to_ground(p_mid, s_mid, raise_out_of_bounds=True)
        assert np.isfinite(lon_m) and np.isfinite(lat_m)
        p_inv, s_inv = g_ohr.ground_to_pixel(lon_m, lat_m, raise_out_of_bounds=False)
        # Safely either inverts or returns NaN (no false coordinates outside Delaunay hull)
        assert np.isnan(p_inv) or p_inv == pytest.approx(p_mid, abs=1.0)

    def test_tmc2_exact_boundaries(self, real_grids):
        _, g_tmc = real_grids
        corners = [
            (g_tmc.pixel_min, g_tmc.scan_min),
            (g_tmc.pixel_max, g_tmc.scan_min),
            (g_tmc.pixel_min, g_tmc.scan_max),
            (g_tmc.pixel_max, g_tmc.scan_max),
        ]

        for p, s in corners:
            assert g_tmc.contains_pixel(p, s) is True
            lon, lat = g_tmc.pixel_to_ground(p, s, raise_out_of_bounds=True)
            assert np.isfinite(lon) and np.isfinite(lat)
            assert g_tmc.lon_min <= lon <= g_tmc.lon_max
            assert g_tmc.lat_min <= lat <= g_tmc.lat_max


# ==============================================================================
# TEST GROUP B: SUB-PIXEL BOUNDARY ATTACK
# ==============================================================================

class TestGroupB_SubPixelBoundaryAttack:
    """Probes coordinates with sub-pixel and floating-point epsilons across boundary lines."""

    @pytest.mark.parametrize("eps", [1e-12, 1e-7, 1e-3, 0.1, 0.5])
    def test_ohrc_boundary_epsilon_transitions(self, real_grids, eps):
        g_ohr, _ = real_grids
        mid_scan = (g_ohr.scan_min + g_ohr.scan_max) / 2.0

        # Epsilon inside pixel_min: valid
        p_in_min = g_ohr.pixel_min + eps
        assert g_ohr.contains_pixel(p_in_min, mid_scan) is True
        lon_in, lat_in = g_ohr.pixel_to_ground(p_in_min, mid_scan)
        assert np.isfinite(lon_in) and np.isfinite(lat_in)

        # Epsilon outside pixel_min: strictly invalid
        p_out_min = g_ohr.pixel_min - eps
        assert g_ohr.contains_pixel(p_out_min, mid_scan) is False
        with pytest.raises(GroundGridOutOfBoundsError):
            g_ohr.pixel_to_ground(p_out_min, mid_scan, raise_out_of_bounds=True)
        lon_out, lat_out = g_ohr.pixel_to_ground(p_out_min, mid_scan, raise_out_of_bounds=False)
        assert np.isnan(lon_out) and np.isnan(lat_out)

        # Epsilon inside pixel_max: valid
        p_in_max = g_ohr.pixel_max - eps
        assert g_ohr.contains_pixel(p_in_max, mid_scan) is True

        # Epsilon outside pixel_max: strictly invalid
        p_out_max = g_ohr.pixel_max + eps
        assert g_ohr.contains_pixel(p_out_max, mid_scan) is False
        with pytest.raises(GroundGridOutOfBoundsError):
            g_ohr.pixel_to_ground(p_out_max, mid_scan, raise_out_of_bounds=True)
        lon_out_max, lat_out_max = g_ohr.pixel_to_ground(p_out_max, mid_scan, raise_out_of_bounds=False)
        assert np.isnan(lon_out_max) and np.isnan(lat_out_max)

    @pytest.mark.parametrize("eps", [1e-9, 1e-5, 0.5])
    def test_scan_boundary_epsilon_transitions(self, real_grids, eps):
        g_ohr, _ = real_grids
        mid_pix = (g_ohr.pixel_min + g_ohr.pixel_max) / 2.0

        # Epsilon outside scan bounds (resolvable above float64 ULP at 78,174)
        s_out_min = g_ohr.scan_min - eps
        s_out_max = g_ohr.scan_max + eps
        assert g_ohr.contains_pixel(mid_pix, s_out_min) is False
        assert g_ohr.contains_pixel(mid_pix, s_out_max) is False

        with pytest.raises(GroundGridOutOfBoundsError):
            g_ohr.pixel_to_ground(mid_pix, s_out_min, raise_out_of_bounds=True)
        with pytest.raises(GroundGridOutOfBoundsError):
            g_ohr.pixel_to_ground(mid_pix, s_out_max, raise_out_of_bounds=True)


# ==============================================================================
# TEST GROUP C: OUT-OF-BOUNDS ATTACK
# ==============================================================================

class TestGroupC_OutOfBoundsAttack:
    """Red-teams the pipeline with negative, extreme, NaN, and Inf coordinate inputs."""

    @pytest.mark.parametrize("hostile_p, hostile_s", [
        (-1.0, 1000.0),
        (1000.0, -1.0),
        (-100.0, -100.0),
        (12000.0, 1000.0),      # Exceeds OHRC 11999.0 max pixel
        (1000.0, 80000.0),      # Exceeds OHRC 78174.0 max scan
        (np.nan, 1000.0),
        (1000.0, np.nan),
        (np.nan, np.nan),
        (np.inf, 1000.0),
        (-np.inf, 1000.0),
        (1000.0, np.inf),
        (1e20, 1e20),
        (-1e20, -1e20),
    ])
    def test_hostile_coordinates_ground_grid(self, real_grids, hostile_p, hostile_s):
        g_ohr, _ = real_grids
        assert g_ohr.contains_pixel(hostile_p, hostile_s) is False

        lon, lat = g_ohr.pixel_to_ground(hostile_p, hostile_s, raise_out_of_bounds=False)
        assert np.isnan(lon) and np.isnan(lat)

        with pytest.raises(GroundGridOutOfBoundsError):
            g_ohr.pixel_to_ground(hostile_p, hostile_s, raise_out_of_bounds=True)

    @pytest.mark.parametrize("hostile_p, hostile_s", [
        (-10.0, 5000.0),
        (15000.0, 5000.0),
        (np.nan, 5000.0),
        (np.inf, 5000.0),
        (1e20, 5000.0),
    ])
    def test_hostile_coordinates_physical_matcher(self, real_physical_engine, hostile_p, hostile_s):
        candidate = real_physical_engine.evaluate_candidate(
            source_pixel=hostile_p,
            source_scan=hostile_s,
            point_id=f"ATTACK_{hostile_p}",
        )
        assert candidate.is_accepted is False
        assert candidate.rejection_reason == "GATE1_SOURCE_OUT_OF_CALIBRATED_GRID"
        assert np.isnan(candidate.longitude) or not np.isfinite(candidate.longitude)
        assert np.isnan(candidate.predicted_target_pixel)


# ==============================================================================
# TEST GROUP D: DEM BOUNDARY ATTACK
# ==============================================================================

class TestGroupD_DEMBoundaryAttack:
    """Evaluates DEMInterface against hostile, out-of-domain, and non-finite queries."""

    def test_dem_exact_boundaries(self, real_dem):
        corners = [
            (real_dem.lon_min, real_dem.lat_min),
            (real_dem.lon_max, real_dem.lat_min),
            (real_dem.lon_min, real_dem.lat_max),
            (real_dem.lon_max, real_dem.lat_max),
        ]
        for lon, lat in corners:
            assert real_dem.contains_coordinate(lon, lat) is True
            h = real_dem.sample(lon, lat, raise_out_of_bounds=True)
            assert np.isfinite(h)
            # Mare Vaporum / Sinus Medii elevations are negative (-2500m to -1000m)
            assert -3500.0 <= h <= 1000.0

    @pytest.mark.parametrize("lon, lat", [
        (22.999, 0.5),          # Just west of lon_min (23.0)
        (24.001, 0.5),          # Just east of lon_max (24.0)
        (23.5, -0.001),         # Just south of lat_min (0.0)
        (23.5, 1.501),          # Just north of lat_max (1.5)
        (np.nan, 0.5),
        (23.5, np.nan),
        (np.inf, 0.5),
        (-np.inf, 0.5),
        (180.0, 0.0),           # Far out on lunar farside
        (-50.0, -80.0),
    ])
    def test_dem_out_of_bounds(self, real_dem, lon, lat):
        assert real_dem.contains_coordinate(lon, lat) is False

        h = real_dem.sample(lon, lat, raise_out_of_bounds=False)
        assert np.isnan(h)

        with pytest.raises(DEMOutOfBoundsError):
            real_dem.sample(lon, lat, raise_out_of_bounds=True)

    def test_physical_matcher_rejects_invalid_dem(self, real_grids):
        g_ohr, g_tmc = real_grids
        # Create a mock DEM covering a different region completely
        mock_dem = DEMInterface(
            elevation_grid=np.full((10, 10), -1800.0, dtype=np.float32),
            lat_min=10.0, lat_max=12.0,  # Far away from OHRC (0.22 - 1.07 N)
            lon_min=50.0, lon_max=52.0,
            resolution_ppd=512.0,
        )
        terrain_geo = TerrainGeometry(ground_grid=g_ohr, dem=mock_dem)
        projector = GridProjector(source_grid=g_ohr, target_grid=g_tmc)
        corridor_calc = TargetCorridorCalculator(projector=projector, terrain_geo=terrain_geo)
        engine = PhysicalCandidateEngine(corridor_calc=corridor_calc)

        # Candidate inside OHRC grid, but missing DEM elevation
        candidate = engine.evaluate_candidate(source_pixel=5000.0, source_scan=30000.0)
        assert candidate.is_accepted is False
        assert candidate.rejection_reason == "GATE2_INVALID_DEM_ELEVATION"


# ==============================================================================
# TEST GROUP E: TARGET SWATH BOUNDARY & SEPARATION INVARIANT
# ==============================================================================

class TestGroupE_TargetSwathBoundary:
    """Verifies that non-overlapping ground swaths and boundary clamping are strictly rejected."""

    def test_real_ohrc_tmc2_swaths_non_overlap_invariance(self, real_physical_engine):
        """Verifies 100% rejection across the real OHRC sensor array due to physical separation."""
        probe_pixels = [100.0, 3000.0, 6000.0, 9000.0, 11800.0]
        probe_scans = [5000.0, 20000.0, 40000.0, 60000.0, 75000.0]

        for p in probe_pixels:
            for s in probe_scans:
                candidate = real_physical_engine.evaluate_candidate(
                    source_pixel=p, source_scan=s, point_id=f"OHRC_{int(p)}_{int(s)}"
                )
                # Must be strictly rejected
                assert candidate.is_accepted is False

                # Safe physical rejection reasons:
                # Target coordinate falls outside calibrated TMC-2 ground domain,
                # or clamps to Delaunay convex hull boundary (pixel == 0),
                # or predicted corridor falls outside target sensor array.
                assert candidate.rejection_reason in {
                    "GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH",
                    "GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY",
                    "GATE6_CORRIDOR_OUTSIDE_TARGET_ARRAY",
                }

    def test_clamping_to_swath_boundary_is_never_accepted(self, real_physical_engine):
        """Verifies Gate 4 specifically detects pixel == 0.0 clamping artifacts."""
        # Find points near the western boundary of the target swath projection
        for s in [10000.0, 30000.0, 50000.0]:
            candidate = real_physical_engine.evaluate_candidate(source_pixel=500.0, source_scan=s)
            assert candidate.is_accepted is False
            if candidate.reference_target_pixel == 0.0:
                assert candidate.rejection_reason == "GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY"


# ==============================================================================
# TEST GROUP F: DATUM CONSISTENCY ATTACK
# ==============================================================================

class TestGroupF_DatumConsistencyAttack:
    """Tests synthetic perturbations and anomalies in datum/coordinate definitions."""

    def test_swapped_lat_lon_coordinates(self, real_grids, real_dem):
        """Swapping latitude and longitude coordinates must cause immediate domain rejection."""
        g_ohr, g_tmc = real_grids
        # Valid OHRC coordinate: Lon ~ 23.4, Lat ~ 0.55
        # Swapped: Lon = 0.55, Lat = 23.4
        swapped_lon = 0.55
        swapped_lat = 23.4

        assert g_ohr.contains_ground(swapped_lon, swapped_lat) is False
        assert real_dem.contains_coordinate(swapped_lon, swapped_lat) is False

        with pytest.raises(GroundGridOutOfBoundsError):
            g_ohr.ground_to_pixel(swapped_lon, swapped_lat, raise_out_of_bounds=True)

        with pytest.raises(DEMOutOfBoundsError):
            real_dem.sample(swapped_lon, swapped_lat, raise_out_of_bounds=True)

    def test_extreme_elevation_datum_offset(self, real_grids, real_dem):
        """Injecting extreme vertical elevation datum offset triggers Gate 5 parallax bounds."""
        g_ohr, g_tmc = real_grids

        # Construct synthetic overlapping grids where Gate 1-4 pass, but elevation is perturbed
        p1 = np.repeat(np.linspace(0, 99, 10), 10).astype(np.int32)
        s1 = np.tile(np.linspace(0, 99, 10), 10).astype(np.int32)
        lon1 = 20.0 + (p1 / 99.0) * 1.0
        lat1 = 0.0 + (s1 / 99.0) * 1.0

        p2 = np.repeat(np.linspace(0, 49, 10), 10).astype(np.int32)
        s2 = np.tile(np.linspace(0, 49, 10), 10).astype(np.int32)
        lon2 = 20.0 + (p2 / 49.0) * 1.0
        lat2 = 0.0 + (s2 / 49.0) * 1.0

        g_src = GroundGrid("src", p1, s1, lon1, lat1, True)
        g_tgt = GroundGrid("tgt", p2, s2, lon2, lat2, True)

        # Hostile DEM with +45,000 m elevation offset (impossible lunar topography)
        hostile_dem = DEMInterface(
            elevation_grid=np.full((10, 10), 45000.0, dtype=np.float32),
            lat_min=-0.5, lat_max=1.5,
            lon_min=19.5, lon_max=21.5,
            resolution_ppd=10.0,
        )
        t_geo = TerrainGeometry(g_src, hostile_dem)
        proj = GridProjector(g_src, g_tgt)
        calc = TargetCorridorCalculator(projector=proj, terrain_geo=t_geo)
        engine = PhysicalCandidateEngine(corridor_calc=calc)

        cand = engine.evaluate_candidate(source_pixel=50.0, source_scan=50.0)
        assert cand.is_accepted is False
        # Parallax displacement exceeds physical maximum of 350 meters
        assert cand.rejection_reason == "GATE5_PARALLAX_EXCEEDS_PHYSICAL_BOUNDS"


# ==============================================================================
# TEST GROUP G: NUMERICAL STABILITY & VECTORIZATION INTEGRITY
# ==============================================================================

class TestGroupG_NumericalStability:
    """Verifies numerical robustness across microscopic deltas, large arrays, and mixed types."""

    def test_microscopic_delta_stability(self, real_grids):
        g_ohr, _ = real_grids
        base_p = 5000.0
        base_s = 35000.0
        tiny_delta = 1e-15

        lon1, lat1 = g_ohr.pixel_to_ground(base_p, base_s)
        lon2, lat2 = g_ohr.pixel_to_ground(base_p + tiny_delta, base_s + tiny_delta)

        assert lon1 == pytest.approx(lon2, abs=1e-12)
        assert lat1 == pytest.approx(lat2, abs=1e-12)

    def test_vectorized_mixed_validity_array(self, real_grids):
        """Asserts vectorized queries do not cross-contaminate valid indices with NaNs."""
        g_ohr, _ = real_grids
        pixels = np.array([5000.0, -10.0, 6000.0, np.nan, 7000.0, np.inf, 12000.0, 8000.0])
        scans = np.array([30000.0, 30000.0, 35000.0, 35000.0, 40000.0, 40000.0, 40000.0, 45000.0])

        valid_mask = g_ohr.contains_pixel(pixels, scans)
        expected_valid = np.array([True, False, True, False, True, False, False, True])
        np.testing.assert_array_equal(valid_mask, expected_valid)

        lons, lats = g_ohr.pixel_to_ground(pixels, scans, raise_out_of_bounds=False)

        # Check that valid indices returned finite numbers within bounds
        for idx in [0, 2, 4, 7]:
            assert np.isfinite(lons[idx]) and np.isfinite(lats[idx])
            assert g_ohr.lon_min <= lons[idx] <= g_ohr.lon_max
            assert g_ohr.lat_min <= lats[idx] <= g_ohr.lat_max

        # Check that invalid indices returned NaN without crashing
        for idx in [1, 3, 5, 6]:
            assert np.isnan(lons[idx]) and np.isnan(lats[idx])

    def test_repeated_queries_determinism(self, real_grids):
        """Repeated identical queries must produce bitwise identical outputs."""
        g_ohr, _ = real_grids
        p_arr = np.full(500, 4567.89, dtype=np.float64)
        s_arr = np.full(500, 12345.67, dtype=np.float64)

        lons, lats = g_ohr.pixel_to_ground(p_arr, s_arr)
        assert np.all(lons == lons[0])
        assert np.all(lats == lats[0])
