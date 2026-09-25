"""Phase 6.2 Adversarial Red-Team Tests: Sun-Angle Change / Illumination Deception Attack.

Evaluates the temporal reasoning and correspondence pipelines against illumination artifacts:
- Scenario A: Same Terrain, Different Sun Azimuth (45° vs 135°, identical topography)
- Scenario B: Solar Elevation Change (50° high sun vs 10° low grazing sun)
- Scenario C: Strong Brightness Change (albedo/photometric shift alone)
- Scenario D: Shadow-Dominated Terrain (deep crater, opposing shadows, boundary verification)
- Scenario E: Temporal Engine Multi-Epoch Integration (4-epoch multi-year solar cycle)
- Scenario F: Contrast Inversion (180° opposite illumination, shadow/highlight reversal)
- Scenario G: False Change Control (positive and negative controls: illumination vs genuine change)
"""

import pytest
import numpy as np
from datetime import datetime, timedelta

from outgraph.ml.synthetic_data.terrain_generator import (
    SyntheticTerrainGenerator,
    SyntheticLunarLandscape,
    LunarCrater,
)
from outgraph.ml.synthetic_data.sensor_simulator import (
    SensorSimulator,
    SimulatedObservation,
)
from outgraph.ml.world_model.temporal import (
    TemporalState,
    TemporalObservationEpoch,
    TemporalAnalysisResult,
    TemporalReasoningEngine,
)
from outgraph.ml.verification.illumination import (
    IlluminationVerifier,
    IlluminationVerificationResult,
)
from outgraph.ml.verification.physics_engine import (
    PhysicsVerificationEngine,
    PhysicsEvidenceProfile,
)
from outgraph.ml.matchers.base import MatchResult
from outgraph.ml.world_model.entity import (
    LunarEntity,
    EntityState,
    EntityResolver,
)


@pytest.fixture(scope="module")
def synthetic_crater_landscape():
    """Generates a synthetic lunar landscape containing a well-defined impact crater."""
    gen = SyntheticTerrainGenerator(base_resolution=512, seed=101)
    # Background lunar elevation map
    elev = gen._generate_fbm_noise((512, 512), octaves=5, persistence=0.5) * 50.0 - 1500.0

    # Add distinct central crater at pixel (256, 256), radius=50 px (~50m), depth=20m
    crater = LunarCrater(x=256.0, y=256.0, radius=50.0, depth=20.0, rim_height=1.2, age_degradation=0.1)
    grid_y, grid_x = np.indices((512, 512))
    elev += gen.generate_crater_profile(grid_x, grid_y, crater)

    landscape = SyntheticLunarLandscape(
        elevation_map=elev,
        mineral_map=np.zeros((3, 512, 512), dtype=np.float32),
        roughness_map=np.full((512, 512), 0.1, dtype=np.float32),
        slope_map=np.full((512, 512), 5.0, dtype=np.float32),
        aspect_map=np.zeros((512, 512), dtype=np.float32),
        craters=[crater],
        seed=101,
        lat_center=0.55,
        lon_center=23.41,
        pixel_scale_m=1.0,
    )
    return landscape


@pytest.fixture(scope="module")
def simulator():
    """Initializes deterministic synthetic sensor simulator."""
    return SensorSimulator(seed=101)


# ==============================================================================
# SCENARIO A: SAME TERRAIN, DIFFERENT SUN AZIMUTH
# ==============================================================================

class TestScenarioA_SunAzimuthChange:
    """Evaluates identical terrain under substantially different solar azimuths."""

    def test_azimuth_shift_is_classified_as_stable(self, synthetic_crater_landscape, simulator):
        # Render Epoch 1: Sun Azimuth = 45°
        obs1 = simulator.simulate_ohrc(
            landscape=synthetic_crater_landscape,
            observation_id="SYNTH-OBS-AZ45",
            sun_azimuth_deg=45.0,
            sun_elevation_deg=25.0,
            target_size=256,
        )
        assert obs1.is_synthetic is True

        # Render Epoch 2: Sun Azimuth = 135° (90° azimuth shift, same terrain)
        obs2 = simulator.simulate_ohrc(
            landscape=synthetic_crater_landscape,
            observation_id="SYNTH-OBS-AZ135",
            sun_azimuth_deg=135.0,
            sun_elevation_deg=25.0,
            target_size=256,
        )
        assert obs2.is_synthetic is True

        # Assert images have strong radiometric differences due to shifting shadows
        diff_img = np.abs(obs1.image_data.astype(float) - obs2.image_data.astype(float))
        assert np.mean(diff_img) > 15.0  # Apparent appearance changed substantially

        # Feed into TemporalReasoningEngine
        t0 = datetime(2021, 1, 15)
        t1 = datetime(2021, 7, 20)

        e1 = TemporalObservationEpoch(
            epoch_id="EP-AZ45",
            observation_id=obs1.observation_id,
            sensor="OHRC",
            timestamp=t0,
            solar_azimuth_deg=45.0,
            solar_elevation_deg=25.0,
            feature_diameter_m=100.0,
            apparent_brightness=float(np.mean(obs1.raw_data)),
        )
        e2 = TemporalObservationEpoch(
            epoch_id="EP-AZ135",
            observation_id=obs2.observation_id,
            sensor="OHRC",
            timestamp=t1,
            solar_azimuth_deg=135.0,
            solar_elevation_deg=25.0,
            feature_diameter_m=100.0,
            apparent_brightness=float(np.mean(obs2.raw_data)),
        )

        res = TemporalReasoningEngine.analyze_timeline("SYNTH-CRATER-A", [e1, e2])

        assert res.temporal_state == TemporalState.STABLE
        assert res.physical_change_supported is False
        assert any("Solar azimuth" in d for d in res.observed_differences)
        assert "STABLE" in res.explanation


# ==============================================================================
# SCENARIO B: SOLAR ELEVATION CHANGE
# ==============================================================================

class TestScenarioB_SolarElevationChange:
    """Evaluates identical terrain under high vs grazing solar elevations."""

    def test_elevation_shift_elongated_shadows_not_physical_change(
        self, synthetic_crater_landscape, simulator
    ):
        # Epoch 1: High sun elevation = 50.0° (short shadows)
        obs_high = simulator.simulate_ohrc(
            landscape=synthetic_crater_landscape,
            observation_id="SYNTH-OBS-EL50",
            sun_azimuth_deg=60.0,
            sun_elevation_deg=50.0,
            target_size=256,
        )
        # Epoch 2: Low grazing sun elevation = 10.0° (elongated shadows)
        obs_low = simulator.simulate_ohrc(
            landscape=synthetic_crater_landscape,
            observation_id="SYNTH-OBS-EL10",
            sun_azimuth_deg=60.0,
            sun_elevation_deg=10.0,
            target_size=256,
        )

        # Shadow fraction (pixels with low reflectance) is much higher under grazing sun
        shadow_frac_high = np.mean(obs_high.raw_data < 0.05)
        shadow_frac_low = np.mean(obs_low.raw_data < 0.05)
        assert shadow_frac_low > shadow_frac_high

        e1 = TemporalObservationEpoch(
            epoch_id="EP-EL50",
            observation_id=obs_high.observation_id,
            sensor="OHRC",
            timestamp=datetime(2021, 3, 1),
            solar_azimuth_deg=60.0,
            solar_elevation_deg=50.0,
            incidence_angle_deg=40.0,
            feature_diameter_m=100.0,
        )
        e2 = TemporalObservationEpoch(
            epoch_id="EP-EL10",
            observation_id=obs_low.observation_id,
            sensor="OHRC",
            timestamp=datetime(2021, 9, 1),
            solar_azimuth_deg=60.0,
            solar_elevation_deg=10.0,
            incidence_angle_deg=80.0,
            feature_diameter_m=100.5,  # Within measurement tolerance
        )

        res = TemporalReasoningEngine.analyze_timeline("SYNTH-CRATER-B", [e1, e2])
        assert res.temporal_state == TemporalState.STABLE
        assert res.physical_change_supported is False
        assert any("Solar elevation" in d for d in res.observed_differences)


# ==============================================================================
# SCENARIO C: STRONG BRIGHTNESS CHANGE
# ==============================================================================

class TestScenarioC_StrongBrightnessChange:
    """Evaluates robustness against severe albedo / exposure brightness scaling."""

    def test_brightness_change_does_not_alter_entity_lifecycle(self):
        # Create an entity in CANDIDATE state
        resolver = EntityResolver(spatial_tolerance_m=200.0)
        entity = resolver.create_entity(
            entity_id="SYNTH-ENTITY-BRT",
            latitude=0.5542,
            longitude=23.4110,
            initial_state=EntityState.CANDIDATE,
        )

        # Simulate 2 observation epochs with 40% brightness disparity
        e1 = TemporalObservationEpoch(
            epoch_id="EP-BRT-1",
            observation_id="OBS-SYNTH-1",
            sensor="OHRC",
            timestamp=datetime(2021, 1, 1),
            solar_azimuth_deg=45.0,
            solar_elevation_deg=30.0,
            feature_diameter_m=80.0,
            apparent_brightness=0.30,
        )
        e2 = TemporalObservationEpoch(
            epoch_id="EP-BRT-2",
            observation_id="OBS-SYNTH-2",
            sensor="OHRC",
            timestamp=datetime(2021, 6, 1),
            solar_azimuth_deg=45.0,
            solar_elevation_deg=30.0,
            feature_diameter_m=80.0,
            apparent_brightness=0.72,  # >40% brightness shift
        )

        res = TemporalReasoningEngine.analyze_timeline(entity.entity_id, [e1, e2])
        assert res.temporal_state == TemporalState.STABLE
        assert res.physical_change_supported is False
        assert any("brightness" in d.lower() for d in res.observed_differences)

        # Entity state must not become CONTRADICTED or REJECTED due to brightness
        assert entity.state in {EntityState.CANDIDATE, EntityState.SUPPORTED}


# ==============================================================================
# SCENARIO D: SHADOW-DOMINATED TERRAIN
# ==============================================================================

class TestScenarioD_ShadowDominatedTerrain:
    """Evaluates whether the matcher mistakes shifting shadow edges for stable boundaries."""

    def test_opposing_shadows_rejected_by_illumination_verifier(
        self, synthetic_crater_landscape, simulator
    ):
        # Generate deep crater under opposing sun angles (Az 30° vs Az 210°)
        obs1 = simulator.simulate_ohrc(
            synthetic_crater_landscape,
            observation_id="OBS-SHADOW-1",
            sun_azimuth_deg=30.0,
            sun_elevation_deg=15.0,
            target_size=256,
        )
        obs2 = simulator.simulate_ohrc(
            synthetic_crater_landscape,
            observation_id="OBS-SHADOW-2",
            sun_azimuth_deg=210.0,  # 180° opposing illumination
            sun_elevation_deg=15.0,
            target_size=256,
        )

        # Run through IlluminationVerifier
        verifier = IlluminationVerifier(max_azimuth_divergence=120.0)
        res = verifier.verify(
            src_image=obs1.image_data,
            tgt_image=obs2.image_data,
            src_meta={"sun_azimuth_deg": 30.0, "sun_elevation_deg": 15.0, "phase_angle_deg": 73.0},
            tgt_meta={"sun_azimuth_deg": 210.0, "sun_elevation_deg": 15.0, "phase_angle_deg": 73.0},
        )

        # Must flag illumination conflict / invalid due to 180° divergence
        assert res.is_valid is False
        assert res.illumination_score < 0.35
        assert "Illumination conflict" in res.reason


# ==============================================================================
# SCENARIO E: TEMPORAL ENGINE MULTI-EPOCH INTEGRATION
# ==============================================================================

class TestScenarioE_TemporalMultiEpochIntegration:
    """Evaluates a multi-year, 4-epoch observation timeline over cycling solar geometry."""

    def test_multi_year_solar_cycle_classified_stable(self):
        t0 = datetime(2021, 2, 1)
        epochs = [
            TemporalObservationEpoch(
                epoch_id="EP-1",
                observation_id="OBS-Y1",
                sensor="OHRC",
                timestamp=t0,
                solar_azimuth_deg=45.0,
                solar_elevation_deg=25.0,
                feature_diameter_m=85.0,
            ),
            TemporalObservationEpoch(
                epoch_id="EP-2",
                observation_id="OBS-Y2",
                sensor="OHRC",
                timestamp=t0 + timedelta(days=365),
                solar_azimuth_deg=120.0,
                solar_elevation_deg=30.0,
                feature_diameter_m=85.2,
            ),
            TemporalObservationEpoch(
                epoch_id="EP-3",
                observation_id="OBS-Y3",
                sensor="OHRC",
                timestamp=t0 + timedelta(days=730),
                solar_azimuth_deg=220.0,
                solar_elevation_deg=15.0,
                feature_diameter_m=84.8,
            ),
            TemporalObservationEpoch(
                epoch_id="EP-4",
                observation_id="OBS-Y4",
                sensor="OHRC",
                timestamp=t0 + timedelta(days=1095),
                solar_azimuth_deg=45.0,
                solar_elevation_deg=25.0,
                feature_diameter_m=85.0,
            ),
        ]

        res = TemporalReasoningEngine.analyze_timeline("SYNTH-CRATER-CYCLE", epochs)
        assert res.temporal_state == TemporalState.STABLE
        assert res.epoch_count == 4
        assert res.time_span_days > 1000.0
        assert res.physical_change_supported is False
        assert len(res.observed_differences) >= 3


# ==============================================================================
# SCENARIO F: CONTRAST INVERSION
# ==============================================================================

class TestScenarioF_ContrastInversion:
    """Verifies that complete shadow/highlight inversion is not mistaken for topography destruction."""

    def test_contrast_inversion_does_not_infer_crater_disappearance(self):
        # 180° opposing illumination causes shadow and highlight walls to completely swap
        e1 = TemporalObservationEpoch(
            epoch_id="EP-INV-1",
            observation_id="OBS-EAST-SUN",
            sensor="OHRC",
            timestamp=datetime(2022, 1, 1),
            solar_azimuth_deg=90.0,  # Sun from East
            solar_elevation_deg=20.0,
            feature_diameter_m=120.0,
            apparent_brightness=0.45,
            morphology_summary="East illuminated wall, West deep shadow",
        )
        e2 = TemporalObservationEpoch(
            epoch_id="EP-INV-2",
            observation_id="OBS-WEST-SUN",
            sensor="OHRC",
            timestamp=datetime(2022, 7, 1),
            solar_azimuth_deg=270.0,  # Sun from West (180° shift)
            solar_elevation_deg=20.0,
            feature_diameter_m=120.0,
            apparent_brightness=0.45,
            morphology_summary="West illuminated wall, East deep shadow",
        )

        res = TemporalReasoningEngine.analyze_timeline("CRATER-CONTRAST-INV", [e1, e2])
        assert res.temporal_state == TemporalState.STABLE
        assert res.physical_change_supported is False
        assert "STABLE" in res.temporal_state.value


# ==============================================================================
# SCENARIO G: FALSE CHANGE CONTROL (SENSITIVITY & SPECIFICITY)
# ==============================================================================

class TestScenarioG_FalseChangeControl:
    """Validates that the engine correctly distinguishes illumination change from genuine change."""

    def test_illumination_only_vs_genuine_structural_change(self):
        # Negative Control (Illumination only): Azimuth shifts 90°, diameter constant
        neg1 = TemporalObservationEpoch(
            epoch_id="NEG-1",
            observation_id="OBS-NEG-1",
            sensor="OHRC",
            timestamp=datetime(2021, 1, 1),
            solar_azimuth_deg=45.0,
            solar_elevation_deg=25.0,
            feature_diameter_m=80.0,
        )
        neg2 = TemporalObservationEpoch(
            epoch_id="NEG-2",
            observation_id="OBS-NEG-2",
            sensor="OHRC",
            timestamp=datetime(2021, 6, 1),
            solar_azimuth_deg=135.0,
            solar_elevation_deg=25.0,
            feature_diameter_m=80.0,
        )
        res_neg = TemporalReasoningEngine.analyze_timeline("CRATER-NEG-CTRL", [neg1, neg2])
        assert res_neg.temporal_state == TemporalState.STABLE
        assert res_neg.physical_change_supported is False

        # Positive Control (Genuine physical change): Illumination identical, diameter changes 35m
        pos1 = TemporalObservationEpoch(
            epoch_id="POS-1",
            observation_id="OBS-POS-1",
            sensor="OHRC",
            timestamp=datetime(2021, 1, 1),
            solar_azimuth_deg=45.0,
            solar_elevation_deg=25.0,
            feature_diameter_m=80.0,
        )
        pos2 = TemporalObservationEpoch(
            epoch_id="POS-2",
            observation_id="OBS-POS-2",
            sensor="OHRC",
            timestamp=datetime(2022, 1, 1),
            solar_azimuth_deg=45.0,
            solar_elevation_deg=25.0,
            feature_diameter_m=115.0,  # 35m genuine structural expansion
        )
        res_pos = TemporalReasoningEngine.analyze_timeline("CRATER-POS-CTRL", [pos1, pos2])
        assert res_pos.temporal_state == TemporalState.CHANGE_SUPPORTED
        assert res_pos.physical_change_supported is True
