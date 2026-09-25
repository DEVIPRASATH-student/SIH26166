"""Calibrated ISRO/ISSDC Ground-Grid Georeferencing Engine.

Provides exact and continuous pixel <-> selenographic coordinate transformations
derived directly from PDS4 geometry grid files (_g_grd_d18.csv).
Eliminates unconstrained planar homography assumptions by using actual
mission-calibrated ground projections.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np
from scipy.interpolate import RegularGridInterpolator, LinearNDInterpolator


class GroundGridError(Exception):
    """Base exception for GroundGrid errors."""
    pass


class GroundGridValidationError(GroundGridError):
    """Raised when ground grid CSV fails validation."""
    pass


class GroundGridOutOfBoundsError(GroundGridError):
    """Raised when query coordinates fall outside the valid calibrated grid domain."""
    pass


class GroundGrid:
    """Calibrated ground-coordinate grid mapping image coordinates (sample, line)
    to selenographic coordinates (longitude, latitude) and vice versa.
    """

    _CACHE: Dict[str, GroundGrid] = {}

    def __init__(
        self,
        source_path: str,
        pixels: np.ndarray,
        scans: np.ndarray,
        lons: np.ndarray,
        lats: np.ndarray,
        is_rectilinear: bool = True,
    ):
        self.source_path = str(source_path)
        self.num_records = len(pixels)

        # Coordinate arrays
        self._raw_pixels = pixels
        self._raw_scans = scans
        self._raw_lons = lons
        self._raw_lats = lats
        self.is_rectilinear = is_rectilinear

        # Sorted unique grid coordinates
        self.unique_pixels = np.unique(pixels)
        self.unique_scans = np.unique(scans)

        # Domain bounds
        self.pixel_min: float = float(self.unique_pixels[0])
        self.pixel_max: float = float(self.unique_pixels[-1])
        self.scan_min: float = float(self.unique_scans[0])
        self.scan_max: float = float(self.unique_scans[-1])

        self.lon_min: float = float(np.min(lons))
        self.lon_max: float = float(np.max(lons))
        self.lat_min: float = float(np.min(lats))
        self.lat_max: float = float(np.max(lats))

        # Forward Interpolator: (scan, pixel) -> (lon, lat)
        if self.is_rectilinear:
            self._build_rectilinear_forward_interpolators()
        else:
            self._build_scattered_forward_interpolators()

        # Inverse Interpolator: (lon, lat) -> (pixel, scan)
        self._inv_pixel: Optional[LinearNDInterpolator] = None
        self._inv_scan: Optional[LinearNDInterpolator] = None

    def _build_rectilinear_forward_interpolators(self):
        """Constructs fast RegularGridInterpolator on 2D rectilinear lattice."""
        n_scan = len(self.unique_scans)
        n_pix = len(self.unique_pixels)

        lon_grid = np.full((n_scan, n_pix), np.nan, dtype=np.float64)
        lat_grid = np.full((n_scan, n_pix), np.nan, dtype=np.float64)

        scan_idx_map = {int(s): i for i, s in enumerate(self.unique_scans)}
        pix_idx_map = {int(p): i for i, p in enumerate(self.unique_pixels)}

        for p, s, lon, lat in zip(self._raw_pixels, self._raw_scans, self._raw_lons, self._raw_lats):
            si = scan_idx_map[int(s)]
            pi = pix_idx_map[int(p)]
            lon_grid[si, pi] = lon
            lat_grid[si, pi] = lat

        self._fwd_lon = RegularGridInterpolator(
            (self.unique_scans, self.unique_pixels),
            lon_grid,
            method="linear",
            bounds_error=False,
            fill_value=np.nan,
        )
        self._fwd_lat = RegularGridInterpolator(
            (self.unique_scans, self.unique_pixels),
            lat_grid,
            method="linear",
            bounds_error=False,
            fill_value=np.nan,
        )

    def _build_scattered_forward_interpolators(self):
        """Fallback scattered forward interpolator if grid is not rectilinear."""
        pts = np.column_stack([self._raw_scans, self._raw_pixels])
        self._fwd_lon = LinearNDInterpolator(pts, self._raw_lons, fill_value=np.nan)
        self._fwd_lat = LinearNDInterpolator(pts, self._raw_lats, fill_value=np.nan)

    def _ensure_inverse_interpolators(self):
        """Constructs inverse interpolator on first demand (lazy initialization)."""
        if self._inv_pixel is None or self._inv_scan is None:
            pts_lonlat = np.column_stack([self._raw_lons, self._raw_lats])
            self._inv_pixel = LinearNDInterpolator(pts_lonlat, self._raw_pixels, fill_value=np.nan)
            self._inv_scan = LinearNDInterpolator(pts_lonlat, self._raw_scans, fill_value=np.nan)

    @classmethod
    def from_csv(cls, csv_path: Union[str, Path], use_cache: bool = True) -> GroundGrid:
        """Loads and validates an ISRO PDS4 _g_grd_d18.csv ground coordinate grid."""
        resolved_path = cls._resolve_path(csv_path)

        if use_cache and str(resolved_path) in cls._CACHE:
            return cls._CACHE[str(resolved_path)]

        if not resolved_path.exists() or not resolved_path.is_file():
            raise FileNotFoundError(f"Ground-grid file not found: {csv_path}")

        pixels: List[int] = []
        scans: List[int] = []
        lons: List[float] = []
        lats: List[float] = []

        with open(resolved_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                raise GroundGridValidationError(f"Empty CSV file: {csv_path}")

            col_map = {col.strip().lower(): i for i, col in enumerate(header)}
            required = ["longitude", "latitude", "pixel", "scan"]
            for req in required:
                if req not in col_map:
                    raise GroundGridValidationError(
                        f"Missing required column '{req}' in {csv_path}. Found columns: {header}"
                    )

            lon_idx = col_map["longitude"]
            lat_idx = col_map["latitude"]
            pix_idx = col_map["pixel"]
            scan_idx = col_map["scan"]

            for line_no, row in enumerate(reader, start=2):
                if not row or len(row) < 4:
                    continue
                try:
                    lon_val = float(row[lon_idx])
                    lat_val = float(row[lat_idx])
                    pix_val = int(round(float(row[pix_idx])))
                    scan_val = int(round(float(row[scan_idx])))
                except (ValueError, IndexError) as err:
                    raise GroundGridValidationError(
                        f"Malformed numeric data in {csv_path} at line {line_no}: {row}"
                    ) from err

                if not np.isfinite(lon_val) or not np.isfinite(lat_val):
                    raise GroundGridValidationError(
                        f"Non-finite coordinates at line {line_no}: lon={lon_val}, lat={lat_val}"
                    )

                lons.append(lon_val)
                lats.append(lat_val)
                pixels.append(pix_val)
                scans.append(scan_val)

        if len(pixels) < 4:
            raise GroundGridValidationError(f"Insufficient grid records in {csv_path} (N={len(pixels)} < 4)")

        pix_arr = np.array(pixels, dtype=np.int32)
        scan_arr = np.array(scans, dtype=np.int32)
        lon_arr = np.array(lons, dtype=np.float64)
        lat_arr = np.array(lats, dtype=np.float64)

        # Verify coordinates uniqueness
        coords_arr = np.column_stack([pix_arr, scan_arr])
        _, unique_indices = np.unique(coords_arr, axis=0, return_index=True)
        if len(unique_indices) != len(coords_arr):
            raise GroundGridValidationError(
                f"Duplicate (pixel, scan) coordinates detected in {csv_path} "
                f"({len(coords_arr) - len(unique_indices)} duplicates)"
            )

        # Verify lattice regularity
        uniq_pix = np.unique(pix_arr)
        uniq_scan = np.unique(scan_arr)
        expected_lattice_size = len(uniq_pix) * len(uniq_scan)
        is_rectilinear = (expected_lattice_size == len(pix_arr))

        instance = cls(
            source_path=str(resolved_path),
            pixels=pix_arr,
            scans=scan_arr,
            lons=lon_arr,
            lats=lat_arr,
            is_rectilinear=is_rectilinear,
        )

        if use_cache:
            cls._CACHE[str(resolved_path)] = instance

        return instance

    @staticmethod
    def _resolve_path(csv_path: Union[str, Path]) -> Path:
        """Resolves file path robustly across workspace subfolders."""
        p = Path(csv_path)
        if p.is_absolute() and p.exists():
            return p
        if p.exists():
            return p.resolve()
        try:
            curr_file = Path(__file__).resolve()
            for parent in curr_file.parents:
                candidate = parent / p
                if candidate.exists():
                    return candidate.resolve()
        except Exception:
            pass
        return p

    def contains_pixel(
        self,
        pixel: Union[float, np.ndarray],
        scan: Union[float, np.ndarray],
    ) -> Union[bool, np.ndarray]:
        """Checks whether (pixel, scan) coordinates fall within the calibrated domain."""
        is_scalar = np.isscalar(pixel) and np.isscalar(scan)
        p = np.asarray(pixel, dtype=np.float64)
        s = np.asarray(scan, dtype=np.float64)

        mask = (p >= self.pixel_min) & (p <= self.pixel_max) & (s >= self.scan_min) & (s <= self.scan_max)
        return bool(mask.item()) if is_scalar else mask

    def contains_ground(
        self,
        lon: Union[float, np.ndarray],
        lat: Union[float, np.ndarray],
    ) -> Union[bool, np.ndarray]:
        """Checks whether (lon, lat) coordinates fall within the valid calibrated ground footprint."""
        is_scalar = np.isscalar(lon) and np.isscalar(lat)
        pix, scan = self.ground_to_pixel(lon, lat, raise_out_of_bounds=False)
        p_arr = np.asarray(pix)
        s_arr = np.asarray(scan)
        valid_mask = np.isfinite(p_arr) & np.isfinite(s_arr)
        return bool(valid_mask.item()) if is_scalar else valid_mask

    def pixel_to_ground(
        self,
        pixel: Union[float, np.ndarray, List[float]],
        scan: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Maps image pixel/sample and scan/line coordinates to selenographic longitude and latitude.

        Args:
            pixel: Image sample coordinate (0 to samples-1).
            scan: Image line/scan coordinate (0 to lines-1).
            raise_out_of_bounds: If True, raises GroundGridOutOfBoundsError on out-of-domain query.

        Returns:
            Tuple of (longitude_deg, latitude_deg). Returns np.nan for out-of-domain points.
        """
        is_scalar = np.isscalar(pixel) and np.isscalar(scan)
        p_arr = np.asarray(pixel, dtype=np.float64)
        s_arr = np.asarray(scan, dtype=np.float64)

        if p_arr.shape != s_arr.shape:
            p_arr, s_arr = np.broadcast_arrays(p_arr, s_arr)

        orig_shape = p_arr.shape
        flat_p = p_arr.ravel()
        flat_s = s_arr.ravel()

        # RegularGridInterpolator expects coords ordered matching grid axes: (scan, pixel)
        coords = np.column_stack([flat_s, flat_p])

        if self.is_rectilinear:
            lons = self._fwd_lon(coords)
            lats = self._fwd_lat(coords)
        else:
            lons = self._fwd_lon(coords)
            lats = self._fwd_lat(coords)

        # Check domain boundaries
        in_domain = (flat_p >= self.pixel_min) & (flat_p <= self.pixel_max) & \
                    (flat_s >= self.scan_min) & (flat_s <= self.scan_max)

        if not np.all(in_domain):
            if raise_out_of_bounds:
                invalid_idx = np.where(~in_domain)[0][0]
                raise GroundGridOutOfBoundsError(
                    f"Pixel query ({flat_p[invalid_idx]}, {flat_s[invalid_idx]}) is outside calibrated domain "
                    f"Pixel=[{self.pixel_min}, {self.pixel_max}], Scan=[{self.scan_min}, {self.scan_max}]"
                )
            lons[~in_domain] = np.nan
            lats[~in_domain] = np.nan

        if is_scalar:
            return float(lons[0]), float(lats[0])

        return lons.reshape(orig_shape), lats.reshape(orig_shape)

    def ground_to_pixel(
        self,
        lon: Union[float, np.ndarray, List[float]],
        lat: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Maps selenographic longitude and latitude to image pixel/sample and scan/line coordinates.

        Args:
            lon: Selenographic longitude in degrees.
            lat: Selenographic latitude in degrees.
            raise_out_of_bounds: If True, raises GroundGridOutOfBoundsError on out-of-domain query.

        Returns:
            Tuple of (pixel, scan). Returns np.nan for points outside the calibrated footprint.
        """
        self._ensure_inverse_interpolators()

        is_scalar = np.isscalar(lon) and np.isscalar(lat)
        lon_arr = np.asarray(lon, dtype=np.float64)
        lat_arr = np.asarray(lat, dtype=np.float64)

        if lon_arr.shape != lat_arr.shape:
            lon_arr, lat_arr = np.broadcast_arrays(lon_arr, lat_arr)

        orig_shape = lon_arr.shape
        flat_lon = lon_arr.ravel()
        flat_lat = lat_arr.ravel()

        coords = np.column_stack([flat_lon, flat_lat])
        pixels = self._inv_pixel(coords)
        scans = self._inv_scan(coords)

        # Check for out-of-bounds (LinearNDInterpolator produces NaN outside convex hull)
        is_nan = np.isnan(pixels) | np.isnan(scans)

        if np.any(is_nan):
            if raise_out_of_bounds:
                nan_idx = np.where(is_nan)[0][0]
                raise GroundGridOutOfBoundsError(
                    f"Ground query (lon={flat_lon[nan_idx]}, lat={flat_lat[nan_idx]}) is outside calibrated footprint "
                    f"Lon=[{self.lon_min:.6f}, {self.lon_max:.6f}], Lat=[{self.lat_min:.6f}, {self.lat_max:.6f}]"
                )

        if is_scalar:
            return float(pixels[0]), float(scans[0])

        return pixels.reshape(orig_shape), scans.reshape(orig_shape)

    def summary(self) -> Dict[str, Any]:
        """Returns structured metadata summary of the ground grid."""
        return {
            "source_path": self.source_path,
            "num_records": self.num_records,
            "is_rectilinear": self.is_rectilinear,
            "unique_pixels_count": len(self.unique_pixels),
            "unique_scans_count": len(self.unique_scans),
            "pixel_bounds": (self.pixel_min, self.pixel_max),
            "scan_bounds": (self.scan_min, self.scan_max),
            "longitude_bounds": (self.lon_min, self.lon_max),
            "latitude_bounds": (self.lat_min, self.lat_max),
        }
