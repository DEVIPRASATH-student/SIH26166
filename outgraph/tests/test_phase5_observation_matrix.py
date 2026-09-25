"""Test Suite for Stage 5.1: Multi-Observation Validation & Compatibility Matrix."""

import pytest

from outgraph.ml.world_model.observation_matrix import (
    OverlapStatus,
    ObservationRecord,
    OverlapEvaluation,
    ObservationCompatibilityMatrix,
)


def test_observation_registration():
    matrix = ObservationCompatibilityMatrix()
    obs = ObservationRecord(
        observation_id="OBS-OHRC-01",
        sensor="OHRC",
        product_id="ch2_ohr_ncp_20210402T0546284043_d_img_d18",
        acquisition_time="2021-04-02T05:46:28",
        gsd_m=0.25,
        lat_bounds=(0.2247, 1.0689),
        lon_bounds=(23.3720, 23.4954),
        has_calibrated_ground_grid=True,
        available_modalities=["OPTICAL_HIGH_RES"],
        provenance={"mission": "Chandrayaan-2"},
    )
    matrix.register_observation(obs)
    assert "OBS-OHRC-01" in matrix.observations
    assert matrix.observations["OBS-OHRC-01"].sensor == "OHRC"
    assert matrix.observations["OBS-OHRC-01"].gsd_m == 0.25


def test_real_ohrc_tmc2_disjoint_footprint_rejection():
    """CRITICAL TEST:

    Verifies that the real OHRC and TMC-2 products in data/real/
    are accurately identified as NO_OVERLAP because of the 1.77 km footprint separation.
    """
    matrix = ObservationCompatibilityMatrix()
    ohrc = ObservationRecord(
        observation_id="OBS-OHRC-REAL",
        sensor="OHRC",
        product_id="ch2_ohr_ncp_20210402T0546284043",
        gsd_m=0.25,
        lat_bounds=(0.2247, 1.0689),
        lon_bounds=(23.3720, 23.4954),
        has_calibrated_ground_grid=True,
    )
    tmc2 = ObservationRecord(
        observation_id="OBS-TMC2-REAL",
        sensor="TMC-2",
        product_id="ch2_tmc_nca_20240523T1600309581",
        gsd_m=5.0,
        lat_bounds=(0.3541, 1.2580),
        lon_bounds=(23.4412, 24.1500),
        has_calibrated_ground_grid=True,
    )
    matrix.register_observation(ohrc)
    matrix.register_observation(tmc2)

    eval_res = matrix.evaluate_compatibility("OBS-OHRC-REAL", "OBS-TMC2-REAL", measured_gap_m=1773.2)
    assert eval_res.overlap_status == OverlapStatus.NO_OVERLAP
    assert eval_res.separation_distance_m == 1773.2
    assert "disjoint" in eval_res.notes.lower()


def test_missing_calibrated_geometry_status():
    matrix = ObservationCompatibilityMatrix()
    obs_cal = ObservationRecord(
        observation_id="OBS-CAL",
        sensor="OHRC",
        gsd_m=0.25,
        lat_bounds=(0.5, 1.0),
        lon_bounds=(23.0, 23.5),
        has_calibrated_ground_grid=True,
    )
    obs_uncal = ObservationRecord(
        observation_id="OBS-UNCAL",
        sensor="IIRS",
        gsd_m=20.0,
        lat_bounds=(0.5, 1.0),
        lon_bounds=(23.0, 23.5),
        has_calibrated_ground_grid=False,
    )
    matrix.register_observation(obs_cal)
    matrix.register_observation(obs_uncal)

    eval_res = matrix.evaluate_compatibility("OBS-CAL", "OBS-UNCAL")
    assert eval_res.overlap_status == OverlapStatus.INSUFFICIENT_GEOMETRY


def test_controlled_synthetic_overlap():
    matrix = ObservationCompatibilityMatrix()
    obs_a = ObservationRecord(
        observation_id="OBS-SYNTH-A",
        sensor="OHRC",
        gsd_m=0.25,
        lat_bounds=(0.5, 1.0),
        lon_bounds=(23.0, 23.5),
        is_synthetic=True,
    )
    obs_b = ObservationRecord(
        observation_id="OBS-SYNTH-B",
        sensor="TMC-2",
        gsd_m=5.0,
        lat_bounds=(0.7, 1.2),
        lon_bounds=(23.2, 23.8),
        is_synthetic=True,
    )
    matrix.register_observation(obs_a)
    matrix.register_observation(obs_b)

    eval_res = matrix.evaluate_compatibility("OBS-SYNTH-A", "OBS-SYNTH-B")
    assert eval_res.overlap_status == OverlapStatus.VALIDATED_OVERLAP


def test_sensor_compatibility_matrix_generation():
    matrix = ObservationCompatibilityMatrix()
    # Register real OHRC and TMC-2
    matrix.register_observation(
        ObservationRecord(
            observation_id="OBS-OHRC",
            sensor="OHRC",
            gsd_m=0.25,
            lat_bounds=(0.2247, 1.0689),
            lon_bounds=(23.3720, 23.4954),
            has_calibrated_ground_grid=True,
        )
    )
    matrix.register_observation(
        ObservationRecord(
            observation_id="OBS-TMC2",
            sensor="TMC-2",
            gsd_m=5.0,
            lat_bounds=(0.3541, 1.2580),
            lon_bounds=(23.4412, 24.1500),
            has_calibrated_ground_grid=True,
        )
    )

    mat = matrix.generate_matrix(["OHRC", "TMC-2", "IIRS", "LROC_NAC", "SELENE_TC"])
    # OHRC <-> TMC-2 must be NO_OVERLAP
    assert mat["OHRC"]["TMC-2"] == OverlapStatus.NO_OVERLAP.value
    assert mat["TMC-2"]["OHRC"] == OverlapStatus.NO_OVERLAP.value

    # IIRS, LROC_NAC, SELENE_TC are unobserved in data/real, so must be UNKNOWN
    assert mat["OHRC"]["IIRS"] == OverlapStatus.UNKNOWN.value
    assert mat["TMC-2"]["LROC_NAC"] == OverlapStatus.UNKNOWN.value
    assert mat["OHRC"]["OHRC"] == "—"
