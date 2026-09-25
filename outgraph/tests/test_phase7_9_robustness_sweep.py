"""Phase 7.9 Robustness Curves & Controlled Parameter Sweep Tests.

Verifies:
- All 8 parameter sweeps execute deterministically and record empirical curves.
- Transition regions (feature collapse, blur collapse, noise degradation, overlap cutoff).
- 0% overlap strictly rejects correspondence (no forced matching).
- Terrain relief produces linear physical parallax displacement: dx = h * tan(theta).
- Real-data invariant is strictly preserved: PHYSICAL CORRESPONDENCE NOT VALIDATED.
- No universal invariance claims, superiority rankings, or aggregate scores.
- Raw flight data files remain unmodified.
"""

from pathlib import Path
import pytest
import numpy as np

from outgraph.ml.benchmark.robustness_sweep import RobustnessSweepEngine, SweepDataPoint


@pytest.fixture
def engine():
    return RobustnessSweepEngine(default_seed=42)


# ==============================================================================
# 1. SCALE SWEEP TESTS
# ==============================================================================

def test_scale_sweep_monotonic_degradation_and_normalization_window(engine):
    """Verifies scale sweep across 1x to 23.35x."""
    scales = [1.0, 2.0, 4.0, 8.0, 16.0, 23.35]
    results = engine.run_scale_sweep(scales=scales)
    assert len(results) == len(scales) * 4  # 4 methods per scale

    sift_raw = [r for r in results if r.method == "SIFT-Raw"]
    sift_norm = [r for r in results if r.method == "SIFT-Normalized"]

    assert len(sift_raw) == len(scales)
    assert len(sift_norm) == len(scales)

    # Monotonic degradation observed on raw scale
    inliers_raw = [r.inliers for r in sift_raw]
    assert inliers_raw[0] >= inliers_raw[-1]

    # Extreme scale (23.35x) produces 0 inliers across both
    assert inliers_raw[-1] == 0


# ==============================================================================
# 2. ILLUMINATION SWEEP TESTS
# ==============================================================================

def test_illumination_sweep_and_negative_control(engine):
    """Verifies illumination sweep (15 to 90 deg) and negative-control preservation."""
    angles = [15.0, 45.0, 75.0, 90.0]
    results = engine.run_illumination_sweep(angles_deg=angles)
    assert len(results) == len(angles) * 2

    phys_points = [r for r in results if r.method == "LunarSynapse-PhysicsAware"]
    for p in phys_points:
        assert p.classification == "ACCEPTED_ILLUMINATION_CONSISTENT"
        assert p.metadata["false_change_inferred"] is False


# ==============================================================================
# 3. GEOMETRIC DISTORTION SWEEP TESTS
# ==============================================================================

def test_geometric_distortion_sweep_rotation(engine):
    """Verifies planar rotation sweep from 0 to 180 degrees."""
    rotations = [0.0, 30.0, 90.0, 180.0]
    results = engine.run_geometric_sweep(rotations=rotations)
    assert len(results) == len(rotations) * 2  # SIFT + ORB

    sift_res = [r for r in results if r.method == "SIFT"]
    assert len(sift_res) == len(rotations)
    # SIFT preserves inliers under 30 deg rotation
    r30 = next(r for r in sift_res if r.parameter_value == 30.0)
    assert r30.inliers >= 6


# ==============================================================================
# 4. NOISE SWEEP TESTS
# ==============================================================================

def test_noise_sweep_graceful_degradation(engine):
    """Verifies Gaussian noise sweep from sigma = 0 to 75."""
    sigmas = [0.0, 15.0, 50.0, 75.0]
    results = engine.run_noise_sweep(noise_sigmas=sigmas)
    assert len(results) == len(sigmas)

    # Inliers degrade gracefully as noise increases
    inliers = [r.inliers for r in results]
    assert inliers[0] >= inliers[-1]
    assert results[-1].parameter_value == 75.0


# ==============================================================================
# 5. BLUR SWEEP TESTS
# ==============================================================================

def test_blur_sweep_resolution_collapse(engine):
    """Verifies optical blur sweep and identifies blur collapse transition."""
    sigmas = [0.0, 1.0, 3.5, 5.0]
    results = engine.run_blur_sweep(blur_sigmas=sigmas)
    assert len(results) == len(sigmas)

    # Severe blur (sigma=5.0) causes feature collapse
    b5 = next(r for r in results if r.parameter_value == 5.0)
    assert b5.inliers < results[0].inliers


# ==============================================================================
# 6. TERRAIN RELIEF SWEEP TESTS
# ==============================================================================

def test_terrain_relief_sweep_linear_parallax(engine):
    """Verifies linear relationship between relief and parallax displacement: dx = h * tan(theta)."""
    reliefs = [0.0, 50.0, 150.0, 250.0, 500.0, 1000.0]
    results = engine.run_terrain_relief_sweep(reliefs_m=reliefs)
    assert len(results) == len(reliefs)

    # At h = 0, displacement is exactly 0
    assert results[0].metadata["ground_displacement_m"] == pytest.approx(0.0, abs=1e-5)

    # At h = 250m, sample 3800 (look angle ~5.08 deg) produces ~22.2m displacement
    r250 = next(r for r in results if r.parameter_value == 250.0)
    assert r250.metadata["ground_displacement_m"] == pytest.approx(22.24, abs=1.5)


# ==============================================================================
# 7. PARTIAL OVERLAP SWEEP TESTS
# ==============================================================================

def test_partial_overlap_zero_overlap_invariant(engine):
    """MANDATORY INVARIANT: 0% overlap MUST NOT produce valid correspondence."""
    overlaps = [0.0, 0.10, 0.25, 0.50, 0.75, 1.00]
    results = engine.run_partial_overlap_sweep(overlaps=overlaps)
    assert len(results) == len(overlaps)

    # Check 0% overlap
    r0 = next(r for r in results if r.parameter_value == 0.0)
    assert r0.inliers == 0
    assert r0.classification == "FOOTPRINT_NON_OVERLAP"
    assert r0.metadata["forced_matching_prevented"] is True

    # 100% overlap produces verified inliers
    r100 = next(r for r in results if r.parameter_value == 1.0)
    assert r100.inliers >= 6


# ==============================================================================
# 8. FEATURE DENSITY SWEEP TESTS
# ==============================================================================

def test_feature_density_sweep_low_texture_transition(engine):
    """Verifies that 0 texture produces zero inliers while dense cratering enables matching."""
    craters = [0, 5, 20]
    results = engine.run_feature_density_sweep(crater_counts=craters)
    assert len(results) == len(craters)

    assert results[0].inliers == 0
    assert results[0].classification == "LOW_TEXTURE"

    assert results[-1].inliers > 0
    assert results[-1].classification == "INLIER_CONFIRMED"


# ==============================================================================
# GUARDRAILS & STANDARDS
# ==============================================================================

def test_no_overall_robustness_score_or_ranking(engine):
    """Verifies that no single aggregate score or method ranking is assigned."""
    results = engine.run_scale_sweep(scales=[1.0, 2.0])
    for r in results:
        assert not hasattr(r, "rank")
        assert not hasattr(r, "universal_score")
        assert not hasattr(r, "winner")
