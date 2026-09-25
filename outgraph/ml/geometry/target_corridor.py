"""Elevation-Bounded Target Corridor Engine.

Constructs physically bounded search corridors in target sensor space (e.g. TMC-2)
representing the range of possible image coordinates admitted by local lunar topography
and parallax uncertainty, rather than predicting an unconstrained point.

Scientific Guardrails & Terminology:
    - Uses strictly the term "Elevation-Bounded Target Corridor".
    - Does NOT use "epipolar corridor" as no full epipolar line is established.
    - Explicitly marks invalid or non-overlapping corridors with structured rejection reasons.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

from .ground_grid import GroundGrid, GroundGridError
from .grid_projection import GridProjector
from .terrain_geometry import TerrainGeometry
from .parallax_model import ParallaxModel, TMC2_PARALLAX_PARAMS, OHRC_PARALLAX_PARAMS


class TargetCorridorError(GroundGridError):
    """Base exception for target corridor calculations."""
    pass


@dataclass(frozen=True)
class CorridorResult:
    """Structured result of an elevation-bounded target corridor computation."""
    ohrc_pixel: float
    ohrc_scan: float
    longitude: float
    latitude: float
    elevation_nominal_m: float
    elevation_min_m: float
    elevation_max_m: float
    reference_tmc_pixel: float
    reference_tmc_scan: float
    corridor_pixel_min: float
    corridor_pixel_max: float
    corridor_scan_min: float
    corridor_scan_max: float
    corridor_width_pixels: float
    corridor_width_meters: float
    is_valid: bool
    rejection_reason: Optional[str] = None


class TargetCorridorCalculator:
    """Calculates elevation-bounded search corridors in target sensor image coordinates."""

    def __init__(
        self,
        projector: GridProjector,
        terrain_geo: TerrainGeometry,
        target_parallax: Optional[ParallaxModel] = None,
        source_parallax: Optional[ParallaxModel] = None,
    ):
        """Initializes corridor calculator.

        Args:
            projector: Reference-datum GridProjector instance.
            terrain_geo: TerrainGeometry instance for source sensor.
            target_parallax: ParallaxModel for target sensor (default TMC-2).
            source_parallax: ParallaxModel for source sensor (default OHRC).
        """
        self.projector = projector
        self.terrain_geo = terrain_geo
        self.target_parallax = target_parallax or ParallaxModel(TMC2_PARALLAX_PARAMS)
        self.source_parallax = source_parallax or ParallaxModel(OHRC_PARALLAX_PARAMS)

    def compute_corridor(
        self,
        ohrc_pixel: float,
        ohrc_scan: float,
        elevation_margin_m: float = 150.0,
        elevation_range: Optional[Tuple[float, float]] = None,
    ) -> CorridorResult:
        """Computes elevation-bounded target corridor for a single OHRC point.

        Args:
            ohrc_pixel: OHRC sample coordinate.
            ohrc_scan: OHRC line/scan coordinate.
            elevation_margin_m: Local topographic uncertainty margin in meters (+/- margin).
            elevation_range: Explicit (min_elevation, max_elevation) bounds; if None, derived from DEM.

        Returns:
            CorridorResult dataclass instance.
        """
        # Step 1: Terrain-aware 3D coordinates
        lon, lat, h_nom = self.terrain_geo.pixel_to_terrain(
            ohrc_pixel, ohrc_scan, use_dem=True, raise_out_of_bounds=False
        )

        if not np.isfinite(lon) or not np.isfinite(lat):
            return CorridorResult(
                ohrc_pixel=float(ohrc_pixel),
                ohrc_scan=float(ohrc_scan),
                longitude=np.nan,
                latitude=np.nan,
                elevation_nominal_m=np.nan,
                elevation_min_m=np.nan,
                elevation_max_m=np.nan,
                reference_tmc_pixel=np.nan,
                reference_tmc_scan=np.nan,
                corridor_pixel_min=np.nan,
                corridor_pixel_max=np.nan,
                corridor_scan_min=np.nan,
                corridor_scan_max=np.nan,
                corridor_width_pixels=0.0,
                corridor_width_meters=0.0,
                is_valid=False,
                rejection_reason="SOURCE_OUT_OF_BOUNDS",
            )

        if not np.isfinite(h_nom):
            return CorridorResult(
                ohrc_pixel=float(ohrc_pixel),
                ohrc_scan=float(ohrc_scan),
                longitude=float(lon),
                latitude=float(lat),
                elevation_nominal_m=np.nan,
                elevation_min_m=np.nan,
                elevation_max_m=np.nan,
                reference_tmc_pixel=np.nan,
                reference_tmc_scan=np.nan,
                corridor_pixel_min=np.nan,
                corridor_pixel_max=np.nan,
                corridor_scan_min=np.nan,
                corridor_scan_max=np.nan,
                corridor_width_pixels=0.0,
                corridor_width_meters=0.0,
                is_valid=False,
                rejection_reason="NO_VALID_DEM_ELEVATION",
            )

        # Step 2: Elevation bounds
        if elevation_range is not None:
            h_min, h_max = elevation_range
        else:
            h_min = h_nom - elevation_margin_m
            h_max = h_nom + elevation_margin_m

        # Step 3: Reference-datum target projection
        tmc_p_ref, tmc_s_ref = self.projector.project_ohrc_to_tmc2(
            ohrc_pixel, ohrc_scan, raise_out_of_bounds=False
        )

        if not np.isfinite(tmc_p_ref) or not np.isfinite(tmc_s_ref):
            return CorridorResult(
                ohrc_pixel=float(ohrc_pixel),
                ohrc_scan=float(ohrc_scan),
                longitude=float(lon),
                latitude=float(lat),
                elevation_nominal_m=float(h_nom),
                elevation_min_m=float(h_min),
                elevation_max_m=float(h_max),
                reference_tmc_pixel=np.nan,
                reference_tmc_scan=np.nan,
                corridor_pixel_min=np.nan,
                corridor_pixel_max=np.nan,
                corridor_scan_min=np.nan,
                corridor_scan_max=np.nan,
                corridor_width_pixels=0.0,
                corridor_width_meters=0.0,
                is_valid=False,
                rejection_reason="TARGET_OUTSIDE_CALIBRATED_SWATH",
            )

        # Step 4: Parallax displacement across elevation interval [h_min, h_max]
        # In TMC-2, cross-track displacement shifts the sample coordinate (pixel)
        dp_min = self.target_parallax.compute_pixel_displacement(h_min, tmc_p_ref)
        dp_max = self.target_parallax.compute_pixel_displacement(h_max, tmc_p_ref)

        p_bound_1 = tmc_p_ref + dp_min
        p_bound_2 = tmc_p_ref + dp_max
        corridor_p_min = min(p_bound_1, p_bound_2)
        corridor_p_max = max(p_bound_1, p_bound_2)

        # Scan variation along flight track is minimal for pushbroom cross-track parallax,
        # but bounded by line integration uncertainty (+/- 1.5 scan lines)
        scan_margin = 2.0
        corridor_s_min = tmc_s_ref - scan_margin
        corridor_s_max = tmc_s_ref + scan_margin

        corridor_width_px = abs(corridor_p_max - corridor_p_min)
        corridor_width_m = corridor_width_px * self.target_parallax.gsd

        # Check if corridor lies within physical sensor boundaries
        tgt_grid = self.projector.target_grid
        is_inside_sensor = (
            corridor_p_max >= tgt_grid.pixel_min
            and corridor_p_min <= tgt_grid.pixel_max
            and corridor_s_max >= tgt_grid.scan_min
            and corridor_s_min <= tgt_grid.scan_max
        )

        rejection_reason = None
        is_valid = bool(is_inside_sensor)

        if not is_inside_sensor:
            if tmc_p_ref == 0.0:
                rejection_reason = "CORRIDOR_CLAMPED_TO_WESTERN_BOUNDARY"
            else:
                rejection_reason = "CORRIDOR_OUTSIDE_TARGET_SENSOR"
        elif tmc_p_ref == 0.0:
            rejection_reason = "CORRIDOR_CLAMPED_TO_WESTERN_BOUNDARY"
            is_valid = False


        return CorridorResult(
            ohrc_pixel=float(ohrc_pixel),
            ohrc_scan=float(ohrc_scan),
            longitude=float(lon),
            latitude=float(lat),
            elevation_nominal_m=float(h_nom),
            elevation_min_m=float(h_min),
            elevation_max_m=float(h_max),
            reference_tmc_pixel=float(tmc_p_ref),
            reference_tmc_scan=float(tmc_s_ref),
            corridor_pixel_min=float(corridor_p_min),
            corridor_pixel_max=float(corridor_p_max),
            corridor_scan_min=float(corridor_s_min),
            corridor_scan_max=float(corridor_s_max),
            corridor_width_pixels=float(corridor_width_px),
            corridor_width_meters=float(corridor_width_m),
            is_valid=is_valid,
            rejection_reason=rejection_reason,
        )

    def compute_corridors_batch(
        self,
        ohrc_pixels: Union[np.ndarray, List[float]],
        ohrc_scans: Union[np.ndarray, List[float]],
        elevation_margin_m: float = 150.0,
    ) -> List[CorridorResult]:
        """Vectorized/batched computation of target corridors."""
        p_arr = np.asarray(ohrc_pixels, dtype=np.float64)
        s_arr = np.asarray(ohrc_scans, dtype=np.float64)

        results = []
        for p, s in zip(p_arr.ravel(), s_arr.ravel()):
            results.append(self.compute_corridor(p, s, elevation_margin_m=elevation_margin_m))
        return results

    def contains_point(
        self,
        corridor: CorridorResult,
        candidate_pixel: float,
        candidate_scan: float,
        tolerance_pixels: float = 1.0,
    ) -> bool:
        """Evaluates whether a candidate target point falls inside the elevation-bounded corridor."""
        if not corridor.is_valid:
            return False

        in_p = (corridor.corridor_pixel_min - tolerance_pixels) <= candidate_pixel <= (corridor.corridor_pixel_max + tolerance_pixels)
        in_s = (corridor.corridor_scan_min - tolerance_pixels) <= candidate_scan <= (corridor.corridor_scan_max + tolerance_pixels)

        return bool(in_p and in_s)
