"""Physically Constrained Correspondence Candidate Engine.

Evaluates potential cross-sensor correspondence candidates using rigorous 3D geometry:
calibrated GroundGrid transformations, SLDEM2015 terrain elevation, and optical
pushbroom parallax corridors.

Strict Scientific Guardrails:
    - NOT a generic appearance/feature matcher.
    - Zero planar homography, RANSAC, or uncalibrated polynomial warps.
    - Requires satisfaction of all six physical geometric gates.
    - If any gate fails, the candidate is explicitly REJECTED with structured physical evidence.
    - Does NOT fabricate correspondence across non-overlapping sensor swaths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

from ..geometry.ground_grid import GroundGrid
from ..geometry.dem_interface import DEMInterface
from ..geometry.terrain_geometry import TerrainGeometry
from ..geometry.parallax_model import ParallaxModel
from ..geometry.target_corridor import TargetCorridorCalculator, CorridorResult


@dataclass(frozen=True)
class PhysicalCandidate:
    """Structured evaluation result for a physical correspondence candidate."""
    point_id: str
    source_pixel: float
    source_scan: float
    longitude: float
    latitude: float
    elevation_m: float
    reference_target_pixel: float
    reference_target_scan: float
    predicted_target_pixel: float
    predicted_target_scan: float
    corridor_bounds: Tuple[float, float, float, float]  # (p_min, p_max, s_min, s_max)
    corridor_width_m: float
    is_accepted: bool
    rejection_reason: Optional[str]
    evidence: Dict[str, Any]


class PhysicalCandidateEngine:
    """Enforces 3D terrain and parallax geometric constraints on correspondence candidates."""

    def __init__(self, corridor_calc: TargetCorridorCalculator):
        """Initializes candidate engine.

        Args:
            corridor_calc: TargetCorridorCalculator instance connecting source and target geometries.
        """
        self.corridor_calc = corridor_calc

    def evaluate_candidate(
        self,
        source_pixel: float,
        source_scan: float,
        point_id: Optional[str] = None,
        elevation_margin_m: float = 150.0,
    ) -> PhysicalCandidate:
        """Evaluates a single source point through the six physical geometric gates.

        Gates:
            Gate 1: Valid Source GroundGrid mapping.
            Gate 2: Valid DEM terrain elevation.
            Gate 3: Target coordinate inside calibrated GroundGrid domain.
            Gate 4: Target coordinate not clamped to swath boundary.
            Gate 5: Parallax displacement physically bounded.
            Gate 6: Elevation-bounded corridor strictly inside target sensor array.

        Returns:
            PhysicalCandidate dataclass instance.
        """
        pid = point_id or f"PT_{int(round(source_pixel))}_{int(round(source_scan))}"

        # Gate 1 & 2: Terrain Geometry & DEM
        corridor = self.corridor_calc.compute_corridor(
            source_pixel, source_scan, elevation_margin_m=elevation_margin_m
        )

        evidence: Dict[str, Any] = {
            "source_coords": (float(source_pixel), float(source_scan)),
            "selenographic_coords": (float(corridor.longitude), float(corridor.latitude)),
            "terrain_elevation_m": float(corridor.elevation_nominal_m),
            "elevation_bounds_m": (float(corridor.elevation_min_m), float(corridor.elevation_max_m)),
            "reference_target_coords": (float(corridor.reference_tmc_pixel), float(corridor.reference_tmc_scan)),
            "corridor_width_m": float(corridor.corridor_width_meters),
        }

        # Check Gate 1: Source validity
        if not np.isfinite(corridor.longitude) or not np.isfinite(corridor.latitude):
            return PhysicalCandidate(
                point_id=pid,
                source_pixel=float(source_pixel),
                source_scan=float(source_scan),
                longitude=np.nan,
                latitude=np.nan,
                elevation_m=np.nan,
                reference_target_pixel=np.nan,
                reference_target_scan=np.nan,
                predicted_target_pixel=np.nan,
                predicted_target_scan=np.nan,
                corridor_bounds=(np.nan, np.nan, np.nan, np.nan),
                corridor_width_m=0.0,
                is_accepted=False,
                rejection_reason="GATE1_SOURCE_OUT_OF_CALIBRATED_GRID",
                evidence=evidence,
            )

        # Check Gate 2: DEM validity
        if not np.isfinite(corridor.elevation_nominal_m):
            return PhysicalCandidate(
                point_id=pid,
                source_pixel=float(source_pixel),
                source_scan=float(source_scan),
                longitude=float(corridor.longitude),
                latitude=float(corridor.latitude),
                elevation_m=np.nan,
                reference_target_pixel=np.nan,
                reference_target_scan=np.nan,
                predicted_target_pixel=np.nan,
                predicted_target_scan=np.nan,
                corridor_bounds=(np.nan, np.nan, np.nan, np.nan),
                corridor_width_m=0.0,
                is_accepted=False,
                rejection_reason="GATE2_INVALID_DEM_ELEVATION",
                evidence=evidence,
            )

        # Check Gate 3: Target calibrated domain
        if not np.isfinite(corridor.reference_tmc_pixel) or not np.isfinite(corridor.reference_tmc_scan):
            return PhysicalCandidate(
                point_id=pid,
                source_pixel=float(source_pixel),
                source_scan=float(source_scan),
                longitude=float(corridor.longitude),
                latitude=float(corridor.latitude),
                elevation_m=float(corridor.elevation_nominal_m),
                reference_target_pixel=np.nan,
                reference_target_scan=np.nan,
                predicted_target_pixel=np.nan,
                predicted_target_scan=np.nan,
                corridor_bounds=(np.nan, np.nan, np.nan, np.nan),
                corridor_width_m=0.0,
                is_accepted=False,
                rejection_reason="GATE3_TARGET_OUTSIDE_CALIBRATED_SWATH",
                evidence=evidence,
            )

        # Check Gate 4: Boundary clamping (artifacts from Delaunay convex hull on non-overlapping strips)
        if corridor.reference_tmc_pixel == 0.0:
            return PhysicalCandidate(
                point_id=pid,
                source_pixel=float(source_pixel),
                source_scan=float(source_scan),
                longitude=float(corridor.longitude),
                latitude=float(corridor.latitude),
                elevation_m=float(corridor.elevation_nominal_m),
                reference_target_pixel=0.0,
                reference_target_scan=float(corridor.reference_tmc_scan),
                predicted_target_pixel=np.nan,
                predicted_target_scan=np.nan,
                corridor_bounds=(
                    corridor.corridor_pixel_min, corridor.corridor_pixel_max,
                    corridor.corridor_scan_min, corridor.corridor_scan_max,
                ),
                corridor_width_m=float(corridor.corridor_width_meters),
                is_accepted=False,
                rejection_reason="GATE4_TARGET_CLAMPED_TO_SWATH_BOUNDARY",
                evidence=evidence,
            )

        # Check Gate 5: Parallax physical limits
        dp = self.corridor_calc.target_parallax.compute_pixel_displacement(
            corridor.elevation_nominal_m, corridor.reference_tmc_pixel
        )
        predicted_p = corridor.reference_tmc_pixel + dp
        predicted_s = corridor.reference_tmc_scan

        evidence["predicted_target_coords"] = (float(predicted_p), float(predicted_s))
        evidence["parallax_pixel_shift"] = float(dp)

        max_allowed_shift_m = 350.0  # Physical lunar maximum
        if abs(dp * self.corridor_calc.target_parallax.gsd) > max_allowed_shift_m:
            return PhysicalCandidate(
                point_id=pid,
                source_pixel=float(source_pixel),
                source_scan=float(source_scan),
                longitude=float(corridor.longitude),
                latitude=float(corridor.latitude),
                elevation_m=float(corridor.elevation_nominal_m),
                reference_target_pixel=float(corridor.reference_tmc_pixel),
                reference_target_scan=float(corridor.reference_tmc_scan),
                predicted_target_pixel=float(predicted_p),
                predicted_target_scan=float(predicted_s),
                corridor_bounds=(
                    corridor.corridor_pixel_min, corridor.corridor_pixel_max,
                    corridor.corridor_scan_min, corridor.corridor_scan_max,
                ),
                corridor_width_m=float(corridor.corridor_width_meters),
                is_accepted=False,
                rejection_reason="GATE5_PARALLAX_EXCEEDS_PHYSICAL_BOUNDS",
                evidence=evidence,
            )

        # Check Gate 6: Corridor inside target sensor bounds
        tgt_grid = self.corridor_calc.projector.target_grid
        corridor_inside = (
            corridor.corridor_pixel_min >= tgt_grid.pixel_min
            and corridor.corridor_pixel_max <= tgt_grid.pixel_max
            and corridor.corridor_scan_min >= tgt_grid.scan_min
            and corridor.corridor_scan_max <= tgt_grid.scan_max
        )

        if not corridor_inside:
            return PhysicalCandidate(
                point_id=pid,
                source_pixel=float(source_pixel),
                source_scan=float(source_scan),
                longitude=float(corridor.longitude),
                latitude=float(corridor.latitude),
                elevation_m=float(corridor.elevation_nominal_m),
                reference_target_pixel=float(corridor.reference_tmc_pixel),
                reference_target_scan=float(corridor.reference_tmc_scan),
                predicted_target_pixel=float(predicted_p),
                predicted_target_scan=float(predicted_s),
                corridor_bounds=(
                    corridor.corridor_pixel_min, corridor.corridor_pixel_max,
                    corridor.corridor_scan_min, corridor.corridor_scan_max,
                ),
                corridor_width_m=float(corridor.corridor_width_meters),
                is_accepted=False,
                rejection_reason="GATE6_CORRIDOR_OUTSIDE_TARGET_ARRAY",
                evidence=evidence,
            )

        # All six gates satisfied
        return PhysicalCandidate(
            point_id=pid,
            source_pixel=float(source_pixel),
            source_scan=float(source_scan),
            longitude=float(corridor.longitude),
            latitude=float(corridor.latitude),
            elevation_m=float(corridor.elevation_nominal_m),
            reference_target_pixel=float(corridor.reference_tmc_pixel),
            reference_target_scan=float(corridor.reference_tmc_scan),
            predicted_target_pixel=float(predicted_p),
            predicted_target_scan=float(predicted_s),
            corridor_bounds=(
                corridor.corridor_pixel_min, corridor.corridor_pixel_max,
                corridor.corridor_scan_min, corridor.corridor_scan_max,
            ),
            corridor_width_m=float(corridor.corridor_width_meters),
            is_accepted=True,
            rejection_reason=None,
            evidence=evidence,
        )

    def evaluate_batch(
        self,
        source_pixels: Union[np.ndarray, List[float]],
        source_scans: Union[np.ndarray, List[float]],
        elevation_margin_m: float = 150.0,
    ) -> List[PhysicalCandidate]:
        """Evaluates a batch of candidate points."""
        p_arr = np.asarray(source_pixels, dtype=np.float64).ravel()
        s_arr = np.asarray(source_scans, dtype=np.float64).ravel()

        results = []
        for i, (p, s) in enumerate(zip(p_arr, s_arr)):
            results.append(
                self.evaluate_candidate(
                    p, s, point_id=f"PT_{i:04d}", elevation_margin_m=elevation_margin_m
                )
            )
        return results
