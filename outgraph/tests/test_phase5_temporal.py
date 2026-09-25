"""Test Suite for Stage 5.4: Temporal Reasoning & Disambiguation Engine."""

import pytest
from datetime import datetime, timedelta

from outgraph.ml.world_model.temporal import (
    TemporalState,
    TemporalObservationEpoch,
    TemporalAnalysisResult,
    TemporalReasoningEngine,
)


def test_single_epoch_insufficient_temporal_evidence():
    t0 = datetime(2021, 3, 19, 10, 55, 0)
    epoch = TemporalObservationEpoch(
        epoch_id="EP-01",
        observation_id="OBS-OHRC-1",
        sensor="OHRC",
        timestamp=t0,
        feature_diameter_m=140.0,
    )

    result = TemporalReasoningEngine.analyze_timeline("ENT-001", [epoch])
    assert result.temporal_state == TemporalState.INSUFFICIENT_TEMPORAL_EVIDENCE
    assert result.epoch_count == 1
    assert result.physical_change_supported is False


def test_illumination_difference_is_not_physical_change():
    """CRITICAL TEST:

    Solar azimuth shift causes apparent brightness / shadow change,
    but feature diameter remains 140m within measurement tolerance.
    Must be classified as STABLE, NEVER physical change.
    """
    t0 = datetime(2021, 3, 19, 10, 55, 0)
    t1 = datetime(2021, 4, 2, 5, 46, 0)

    e1 = TemporalObservationEpoch(
        epoch_id="EP-01",
        observation_id="OBS-OHRC-T1",
        sensor="OHRC",
        timestamp=t0,
        solar_azimuth_deg=45.0,
        solar_elevation_deg=22.0,
        feature_diameter_m=140.0,
        apparent_brightness=0.35,
    )
    e2 = TemporalObservationEpoch(
        epoch_id="EP-02",
        observation_id="OBS-OHRC-T2",
        sensor="OHRC",
        timestamp=t1,
        solar_azimuth_deg=135.0,  # 90° azimuth shift!
        solar_elevation_deg=18.0,
        feature_diameter_m=140.5,  # Within 3m tolerance
        apparent_brightness=0.62,  # Brightness changed significantly
    )

    result = TemporalReasoningEngine.analyze_timeline("ENT-001", [e1, e2])
    assert result.temporal_state == TemporalState.STABLE
    assert result.physical_change_supported is False
    assert any("Solar azimuth" in d for d in result.observed_differences)
    assert "STABLE" in result.explanation


def test_genuine_physical_change_supported():
    """Consistent viewing geometry with significant diameter expansion (e.g. fresh collapse)."""
    t0 = datetime(2021, 3, 19)
    t1 = datetime(2022, 3, 19)

    e1 = TemporalObservationEpoch(
        epoch_id="EP-01",
        observation_id="OBS-T1",
        sensor="OHRC",
        timestamp=t0,
        solar_azimuth_deg=45.0,
        solar_elevation_deg=22.0,
        feature_diameter_m=140.0,
    )
    e2 = TemporalObservationEpoch(
        epoch_id="EP-02",
        observation_id="OBS-T2",
        sensor="OHRC",
        timestamp=t1,
        solar_azimuth_deg=46.0,  # Nearly identical illumination
        solar_elevation_deg=21.5,
        feature_diameter_m=168.0,  # 28m structural change!
    )

    result = TemporalReasoningEngine.analyze_timeline("ENT-001", [e1, e2])
    assert result.temporal_state == TemporalState.CHANGE_SUPPORTED
    assert result.physical_change_supported is True
    assert "CHANGE_SUPPORTED" in result.temporal_state.value


def test_ambiguous_change_possible_change():
    """Both solar angle and geometry changed; cannot conclusively separate illumination from physical."""
    t0 = datetime(2021, 3, 19)
    t1 = datetime(2022, 3, 19)

    e1 = TemporalObservationEpoch(
        epoch_id="EP-01",
        observation_id="OBS-T1",
        sensor="OHRC",
        timestamp=t0,
        solar_azimuth_deg=45.0,
        feature_diameter_m=140.0,
    )
    e2 = TemporalObservationEpoch(
        epoch_id="EP-02",
        observation_id="OBS-T2",
        sensor="OHRC",
        timestamp=t1,
        solar_azimuth_deg=145.0,  # Big illumination shift
        feature_diameter_m=148.0,  # 8m diameter shift
    )

    result = TemporalReasoningEngine.analyze_timeline("ENT-001", [e1, e2])
    assert result.temporal_state == TemporalState.POSSIBLE_CHANGE
    assert result.physical_change_supported is False


def test_contradicted_temporal_change():
    t0 = datetime(2021, 3, 19)
    t1 = datetime(2022, 3, 19)

    e1 = TemporalObservationEpoch(
        epoch_id="EP-01",
        observation_id="OBS-T1",
        sensor="OHRC",
        timestamp=t0,
    )
    e2 = TemporalObservationEpoch(
        epoch_id="EP-02",
        observation_id="OBS-T2",
        sensor="OHRC",
        timestamp=t1,
        notes="CONTRADICTED: artifact verified as transient shadow boundary",
    )

    result = TemporalReasoningEngine.analyze_timeline("ENT-001", [e1, e2])
    assert result.temporal_state == TemporalState.CHANGE_CONTRADICTED
    assert result.physical_change_supported is False
