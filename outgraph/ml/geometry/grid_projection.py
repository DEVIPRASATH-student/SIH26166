"""Calibrated Reference-Datum Grid-to-Grid Projection Engine.

Provides exact and continuous reference-surface projection between sensor geometries:
    Source Sensor (e.g. OHRC) Pixel/Scan
        ↓
    Source GroundGrid (Forward Interpolation)
        ↓
    Calibrated Selenographic Coordinates (Longitude, Latitude)
        ↓
    Target GroundGrid (Inverse Interpolation)
        ↓
    Predicted Target Sensor (e.g. TMC-2) Pixel/Scan

Scientific Terminology & Physical Guardrails:
    - This projection is strictly a "Reference-Datum Projection" or "Reference-Surface Projection".
    - It maps coordinates across the ISRO calibrated reference spheroid/datum.
    - It does NOT establish physical 3D correspondence between image observations.
    - It does NOT replace DEM-derived elevation, parallax, or epipolar corridor modeling.
    - It completely avoids planar homography, RANSAC, or uncalibrated polynomial warps.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

from .ground_grid import GroundGrid, GroundGridOutOfBoundsError, GroundGridError


class GridProjectionError(GroundGridError):
    """Base exception for grid projection operations."""
    pass


class GridProjector:
    """Calibrated reference-datum grid-to-grid projector between sensor geometries.

    Maps image coordinates from a source sensor across calibrated selenographic
    ground coordinates to predicted image coordinates in a target sensor on the
    lunar reference datum.
    """

    def __init__(self, source_grid: GroundGrid, target_grid: GroundGrid):
        """Initializes the reference-datum grid projector.

        Args:
            source_grid: Calibrated GroundGrid for source sensor (e.g., OHRC).
            target_grid: Calibrated GroundGrid for target sensor (e.g., TMC-2).
        """
        if not isinstance(source_grid, GroundGrid) or not isinstance(target_grid, GroundGrid):
            raise TypeError("Both source_grid and target_grid must be instances of GroundGrid")

        self.source_grid = source_grid
        self.target_grid = target_grid

    def project_source_to_target(
        self,
        pixel: Union[float, np.ndarray, List[float]],
        scan: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Maps coordinates from source pixel space to target pixel space via reference datum.

        Workflow:
            1. (src_pixel, src_scan) -> (lon, lat) via source_grid.pixel_to_ground()
            2. (lon, lat) -> (tgt_pixel, tgt_scan) via target_grid.ground_to_pixel()

        Args:
            pixel: Source sensor pixel/sample coordinate(s).
            scan: Source sensor scan/line coordinate(s).
            raise_out_of_bounds: If True, raises GroundGridOutOfBoundsError when any coordinate
                falls outside the source or target calibrated domains. If False, returns np.nan.

        Returns:
            Tuple of (predicted_target_pixel, predicted_target_scan).
        """
        lons, lats = self.source_grid.pixel_to_ground(pixel, scan, raise_out_of_bounds=raise_out_of_bounds)
        tgt_pixels, tgt_scans = self.target_grid.ground_to_pixel(lons, lats, raise_out_of_bounds=raise_out_of_bounds)
        return tgt_pixels, tgt_scans

    def project_target_to_source(
        self,
        pixel: Union[float, np.ndarray, List[float]],
        scan: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Inverse projection: maps coordinates from target pixel space to source pixel space.

        Workflow:
            1. (tgt_pixel, tgt_scan) -> (lon, lat) via target_grid.pixel_to_ground()
            2. (lon, lat) -> (src_pixel, src_scan) via source_grid.ground_to_pixel()

        Args:
            pixel: Target sensor pixel/sample coordinate(s).
            scan: Target sensor scan/line coordinate(s).
            raise_out_of_bounds: If True, raises GroundGridOutOfBoundsError on out-of-domain query.

        Returns:
            Tuple of (predicted_source_pixel, predicted_source_scan).
        """
        lons, lats = self.target_grid.pixel_to_ground(pixel, scan, raise_out_of_bounds=raise_out_of_bounds)
        src_pixels, src_scans = self.source_grid.ground_to_pixel(lons, lats, raise_out_of_bounds=raise_out_of_bounds)
        return src_pixels, src_scans

    def project_ohrc_to_tmc2(
        self,
        ohrc_pixel: Union[float, np.ndarray, List[float]],
        ohrc_scan: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Convenience method projecting OHRC pixel/scan to predicted TMC-2 pixel/scan."""
        return self.project_source_to_target(ohrc_pixel, ohrc_scan, raise_out_of_bounds=raise_out_of_bounds)

    def project_tmc2_to_ohrc(
        self,
        tmc_pixel: Union[float, np.ndarray, List[float]],
        tmc_scan: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Convenience method projecting TMC-2 pixel/scan to predicted OHRC pixel/scan."""
        return self.project_target_to_source(tmc_pixel, tmc_scan, raise_out_of_bounds=raise_out_of_bounds)

    def is_ground_in_target_domain(
        self,
        lon: Union[float, np.ndarray, List[float]],
        lat: Union[float, np.ndarray, List[float]],
    ) -> Union[bool, np.ndarray]:
        """Checks whether selenographic coordinates fall inside the target sensor's calibrated footprint."""
        return self.target_grid.contains_ground(lon, lat)

    def is_source_in_target_domain(
        self,
        src_pixel: Union[float, np.ndarray, List[float]],
        src_scan: Union[float, np.ndarray, List[float]],
    ) -> Union[bool, np.ndarray]:
        """Checks whether source sensor coordinates project inside the target sensor's calibrated footprint."""
        lons, lats = self.source_grid.pixel_to_ground(src_pixel, src_scan, raise_out_of_bounds=False)
        is_scalar = np.isscalar(lons) and np.isscalar(lats)
        lon_arr = np.asarray(lons)
        lat_arr = np.asarray(lats)

        valid_source = np.isfinite(lon_arr) & np.isfinite(lat_arr)
        result = np.zeros(valid_source.shape, dtype=bool)

        if np.any(valid_source):
            in_tgt = self.target_grid.contains_ground(lon_arr[valid_source], lat_arr[valid_source])
            result[valid_source] = in_tgt

        return bool(result.item()) if is_scalar else result

    def get_geographic_overlap(self) -> Dict[str, Any]:
        """Calculates geographic footprint domains and bounding box intersection."""
        src = self.source_grid
        tgt = self.target_grid

        lon_min = max(src.lon_min, tgt.lon_min)
        lon_max = min(src.lon_max, tgt.lon_max)
        lat_min = max(src.lat_min, tgt.lat_min)
        lat_max = min(src.lat_max, tgt.lat_max)

        has_bbox_overlap = bool((lon_min < lon_max) and (lat_min < lat_max))
        bbox_overlap = {
            "lon_min": float(lon_min) if has_bbox_overlap else None,
            "lon_max": float(lon_max) if has_bbox_overlap else None,
            "lat_min": float(lat_min) if has_bbox_overlap else None,
            "lat_max": float(lat_max) if has_bbox_overlap else None,
            "has_overlap": has_bbox_overlap,
        }

        return {
            "source_bounds": {
                "lon_min": src.lon_min,
                "lon_max": src.lon_max,
                "lat_min": src.lat_min,
                "lat_max": src.lat_max,
            },
            "target_bounds": {
                "lon_min": tgt.lon_min,
                "lon_max": tgt.lon_max,
                "lat_min": tgt.lat_min,
                "lat_max": tgt.lat_max,
            },
            "bbox_intersection": bbox_overlap,
        }

    def compute_round_trip_residuals(
        self,
        src_pixel: Union[float, np.ndarray, List[float]],
        src_scan: Union[float, np.ndarray, List[float]],
        moon_radius_km: float = 1737.4,
    ) -> Dict[str, Any]:
        """Evaluates round-trip consistency of the reference-datum projection.

        Path:
            (src_pixel, src_scan)
                ↓ [source_grid.pixel_to_ground]
            (lon, lat)
                ↓ [target_grid.ground_to_pixel]
            (tgt_pixel, tgt_scan)
                ↓ [target_grid.pixel_to_ground]
            (lon', lat')

        Measures residual:
            delta_lon = lon' - lon
            delta_lat = lat' - lat

        Args:
            src_pixel: Source sensor pixel/sample coordinate(s).
            src_scan: Source sensor scan/line coordinate(s).
            moon_radius_km: Mean volumetric lunar radius in km (default 1737.4 km).

        Returns:
            Dictionary containing tested points count, valid/invalid counts,
            residual arrays, and summary statistics.
        """
        is_scalar = np.isscalar(src_pixel) and np.isscalar(src_scan)
        p_arr = np.asarray(src_pixel, dtype=np.float64)
        s_arr = np.asarray(src_scan, dtype=np.float64)

        if p_arr.shape != s_arr.shape:
            p_arr, s_arr = np.broadcast_arrays(p_arr, s_arr)

        flat_p = p_arr.ravel()
        flat_s = s_arr.ravel()
        total_count = len(flat_p)

        # Step 1: Forward source
        lons, lats = self.source_grid.pixel_to_ground(flat_p, flat_s, raise_out_of_bounds=False)

        # Step 2: Target inverse
        tgt_p, tgt_s = self.target_grid.ground_to_pixel(lons, lats, raise_out_of_bounds=False)

        valid_mask = np.isfinite(tgt_p) & np.isfinite(tgt_s)
        valid_count = int(np.sum(valid_mask))
        invalid_count = total_count - valid_count

        if valid_count == 0:
            return {
                "total_points": total_count,
                "valid_count": 0,
                "invalid_count": total_count,
                "valid_mask": valid_mask.reshape(p_arr.shape) if not is_scalar else bool(valid_mask[0]),
                "delta_lon_deg": np.array([]),
                "delta_lat_deg": np.array([]),
                "ground_residual_m": np.array([]),
                "statistics": None,
            }

        # Step 3: Target forward back-projection
        lons_prime, lats_prime = self.target_grid.pixel_to_ground(
            tgt_p[valid_mask], tgt_s[valid_mask], raise_out_of_bounds=False
        )

        d_lon = lons_prime - lons[valid_mask]
        d_lat = lats_prime - lats[valid_mask]

        r_m = moon_radius_km * 1000.0
        rad_conv = np.pi / 180.0
        lat_m = d_lat * rad_conv * r_m
        lon_m = d_lon * rad_conv * r_m * np.cos(np.radians(lats[valid_mask]))
        ground_dist_m = np.sqrt(lat_m**2 + lon_m**2)

        stats = {
            "mean_delta_lon_deg": float(np.mean(np.abs(d_lon))),
            "max_delta_lon_deg": float(np.max(np.abs(d_lon))),
            "mean_delta_lat_deg": float(np.mean(np.abs(d_lat))),
            "max_delta_lat_deg": float(np.max(np.abs(d_lat))),
            "mean_ground_residual_m": float(np.mean(ground_dist_m)),
            "median_ground_residual_m": float(np.median(ground_dist_m)),
            "max_ground_residual_m": float(np.max(ground_dist_m)),
            "min_ground_residual_m": float(np.min(ground_dist_m)),
            "std_ground_residual_m": float(np.std(ground_dist_m)),
        }

        return {
            "total_points": total_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "valid_mask": valid_mask.reshape(p_arr.shape) if not is_scalar else bool(valid_mask[0]),
            "delta_lon_deg": d_lon,
            "delta_lat_deg": d_lat,
            "ground_residual_m": ground_dist_m,
            "statistics": stats,
        }
