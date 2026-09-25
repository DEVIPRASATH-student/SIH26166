"""Temporal Reasoning Engine for Lunar World Model.
Stage 5.4: Multi-Epoch Temporal Analysis & Observational vs Physical Change Disambiguation.

Enforces:
1. Strict disambiguation between OBSERVATIONAL DIFFERENCE (solar azimuth, incidence, shadow angles)
   and GENUINE PHYSICAL CHANGE (impact cratering, boulder fall).
2. Explicit states:
   - STABLE
   - POSSIBLE_CHANGE
   - CHANGE_SUPPORTED
   - CHANGE_CONTRADICTED
   - INSUFFICIENT_TEMPORAL_EVIDENCE
3. Zero false-positive change detections triggered solely by illumination or phase angle shifts.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any
import math
from pydantic import BaseModel, Field


class TemporalState(str, Enum):
    """Scientific classification of temporal stability or change."""
    STABLE = "STABLE"
    POSSIBLE_CHANGE = "POSSIBLE_CHANGE"
    CHANGE_SUPPORTED = "CHANGE_SUPPORTED"
    CHANGE_CONTRADICTED = "CHANGE_CONTRADICTED"
    INSUFFICIENT_TEMPORAL_EVIDENCE = "INSUFFICIENT_TEMPORAL_EVIDENCE"


class TemporalObservationEpoch(BaseModel):
    """Observation parameters and measurements for an entity at a specific point in time."""
    epoch_id: str
    observation_id: str
    sensor: str
    timestamp: datetime
    solar_azimuth_deg: Optional[float] = None
    solar_elevation_deg: Optional[float] = None
    incidence_angle_deg: Optional[float] = None
    feature_diameter_m: Optional[float] = None
    apparent_brightness: Optional[float] = None
    morphology_summary: Optional[str] = None
    notes: Optional[str] = None

    model_config = {"frozen": False}


class TemporalAnalysisResult(BaseModel):
    """Synthesis of temporal reasoning across multiple observation epochs."""
    entity_id: str
    temporal_state: TemporalState
    epoch_count: int
    time_span_days: float
    observed_differences: List[str] = Field(default_factory=list)
    physical_change_supported: bool
    explanation: str
    confidence: Optional[float] = None

    model_config = {"frozen": False}


class TemporalReasoningEngine:
    """Evaluates time-series observations to detect physical changes while filtering illumination artifacts."""

    @classmethod
    def analyze_timeline(
        cls,
        entity_id: str,
        epochs: List[TemporalObservationEpoch],
        measurement_tolerance_m: float = 3.0,
    ) -> TemporalAnalysisResult:
        """Analyzes observation epochs sorted chronologically."""
        if len(epochs) < 2:
            return TemporalAnalysisResult(
                entity_id=entity_id,
                temporal_state=TemporalState.INSUFFICIENT_TEMPORAL_EVIDENCE,
                epoch_count=len(epochs),
                time_span_days=0.0,
                observed_differences=[],
                physical_change_supported=False,
                explanation="Only a single observation epoch recorded; temporal evolution unconstrained.",
            )

        # Sort epochs by timestamp
        sorted_epochs = sorted(epochs, key=lambda e: e.timestamp)
        t_span = (sorted_epochs[-1].timestamp - sorted_epochs[0].timestamp).total_seconds() / 86400.0

        differences = []
        has_illumination_shift = False
        has_geometric_shift = False
        contradicted_claim = False

        for i in range(len(sorted_epochs) - 1):
            e1 = sorted_epochs[i]
            e2 = sorted_epochs[i + 1]

            # Check illumination differences
            if e1.solar_azimuth_deg is not None and e2.solar_azimuth_deg is not None:
                d_az = abs(e1.solar_azimuth_deg - e2.solar_azimuth_deg) % 360.0
                if d_az > 180.0:
                    d_az = 360.0 - d_az
                if d_az > 10.0:
                    has_illumination_shift = True
                    differences.append(f"Solar azimuth shifted by {d_az:.1f}° between {e1.epoch_id} and {e2.epoch_id}.")

            if e1.solar_elevation_deg is not None and e2.solar_elevation_deg is not None:
                d_el = abs(e1.solar_elevation_deg - e2.solar_elevation_deg)
                if d_el > 5.0:
                    has_illumination_shift = True
                    differences.append(f"Solar elevation shifted by {d_el:.1f}° between {e1.epoch_id} and {e2.epoch_id}.")

            if e1.incidence_angle_deg is not None and e2.incidence_angle_deg is not None:
                d_inc = abs(e1.incidence_angle_deg - e2.incidence_angle_deg)
                if d_inc > 5.0:
                    has_illumination_shift = True
                    differences.append(f"Solar incidence angle shifted by {d_inc:.1f}° between {e1.epoch_id} and {e2.epoch_id}.")

            if e1.apparent_brightness is not None and e2.apparent_brightness is not None:
                d_br = abs(e1.apparent_brightness - e2.apparent_brightness)
                if d_br > 0.15:
                    has_illumination_shift = True
                    differences.append(f"Apparent pixel brightness shifted by {d_br:.2f}.")

            # Check physical geometric differences (e.g. crater diameter)
            if e1.feature_diameter_m is not None and e2.feature_diameter_m is not None:
                d_diam = abs(e1.feature_diameter_m - e2.feature_diameter_m)
                if d_diam > measurement_tolerance_m:
                    has_geometric_shift = True
                    differences.append(f"Physical diameter shifted by {d_diam:.1f}m (exceeds {measurement_tolerance_m}m tolerance).")

            # Check for contradiction flags in notes
            if "CONTRADICTED" in (e1.notes or "") or "CONTRADICTED" in (e2.notes or ""):
                contradicted_claim = True

        # Synthesis
        if contradicted_claim:
            state = TemporalState.CHANGE_CONTRADICTED
            explanation = "Temporal change claim contradicted by higher-resolution observation or calibration check."
            change_supported = False
        elif has_geometric_shift and not has_illumination_shift:
            state = TemporalState.CHANGE_SUPPORTED
            explanation = "Significant structural geometric change verified under consistent viewing geometry."
            change_supported = True
        elif has_illumination_shift and not has_geometric_shift:
            # Critical scientific rule: Illumination differences do NOT constitute physical change!
            state = TemporalState.STABLE
            explanation = "Observational differences detected (solar azimuth/incidence angle shift), but physical structure remains STABLE."
            change_supported = False
        elif has_geometric_shift and has_illumination_shift:
            state = TemporalState.POSSIBLE_CHANGE
            explanation = "Apparent geometric differences observed alongside significant solar angle shifts; requires normalized illumination validation."
            change_supported = False
        else:
            state = TemporalState.STABLE
            explanation = "Feature is temporally stable; measurements consistent across observation epochs."
            change_supported = False

        return TemporalAnalysisResult(
            entity_id=entity_id,
            temporal_state=state,
            epoch_count=len(sorted_epochs),
            time_span_days=round(t_span, 2),
            observed_differences=differences,
            physical_change_supported=change_supported,
            explanation=explanation,
        )
