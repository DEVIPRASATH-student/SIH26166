"""Authoritative Lunar Digital Elevation Model (DEM) Interface.

Provides exact and continuous terrain elevation sampling derived directly from
the NASA/JAXA SLDEM2015 (merged LOLA and SELENE/Kaguya Terrain Camera) dataset.
Supports sub-pixel bilinear interpolation, vectorized coordinate arrays,
and explicit out-of-domain / no-data boundary rejection.

Scientific Terminology & Physical Guardrails:
    - Reports "DEM Terrain Elevation" (h) in meters relative to the 1737.4 km lunar sphere.
    - Clearly distinguishes the reference datum (h = 0) from the physical terrain surface.
    - Out-of-bounds coordinates return np.nan or raise DEMOutOfBoundsError.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

from .ground_grid import GroundGridError


class DEMError(GroundGridError):
    """Base exception for digital elevation model errors."""
    pass


class DEMOutOfBoundsError(DEMError):
    """Raised when query coordinates fall outside the valid calibrated DEM domain."""
    pass


class DEMInterface:
    """Interface for sampling elevation from authoritative Lunar DEMs (SLDEM2015 / LOLA)."""

    DEFAULT_BUFFERED_PATH = "data/real/dem/sldem2015_ohrc_buffered.npz"
    DEFAULT_JP2_PATH = "data/real/dem/SLDEM2015_512_00N_30N_000_045.JP2"
    DEFAULT_LBL_PATH = "data/real/dem/SLDEM2015_512_00N_30N_000_045_JP2.LBL"

    _INSTANCE: Optional[DEMInterface] = None

    def __init__(
        self,
        elevation_grid: np.ndarray,
        lat_min: float,
        lat_max: float,
        lon_min: float,
        lon_max: float,
        resolution_ppd: float = 512.0,
        reference_radius_km: float = 1737.4,
        nodata_value: float = -32768.0,
        source_name: str = "SLDEM2015_512_00N_30N_000_045",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initializes DEM raster interface.

        Args:
            elevation_grid: 2D array of elevations in meters (lines, samples).
            lat_min: Minimum latitude in degrees (southern edge).
            lat_max: Maximum latitude in degrees (northern edge).
            lon_min: Minimum longitude in degrees (western edge).
            lon_max: Maximum longitude in degrees (eastern edge).
            resolution_ppd: Map resolution in pixels per degree.
            reference_radius_km: Reference sphere radius (default 1737.4 km).
            nodata_value: Fill / missing value indicator.
            source_name: Product identifier.
            metadata: Structured provenance metadata.
        """
        self.elevation = np.asarray(elevation_grid, dtype=np.float32)
        self.n_lines, self.n_samples = self.elevation.shape
        self.lat_min = float(lat_min)
        self.lat_max = float(lat_max)
        self.lon_min = float(lon_min)
        self.lon_max = float(lon_max)
        self.resolution_ppd = float(resolution_ppd)
        self.reference_radius_km = float(reference_radius_km)
        self.nodata_value = float(nodata_value)
        self.source_name = str(source_name)
        self.metadata = metadata or {}

        # Derived grid coordinates
        self.lats = np.linspace(self.lat_max, self.lat_min, self.n_lines)
        self.lons = np.linspace(self.lon_min, self.lon_max, self.n_samples)

    @classmethod
    def load_default(cls, use_cache: bool = True) -> DEMInterface:
        """Loads default SLDEM2015 DEM covering the OHRC region."""
        if use_cache and cls._INSTANCE is not None:
            return cls._INSTANCE

        buf_path = cls._resolve_path(cls.DEFAULT_BUFFERED_PATH)
        if buf_path.exists():
            data = np.load(buf_path)
            meta = {
                "source_organization": "NASA / JAXA / MIT PDS Node",
                "product_name": "SLDEM2015_512_00N_30N_000_045",
                "product_version": "V2.0",
                "source_url": "http://imbrium.mit.edu/DATA/SLDEM2015/TILES/JP2/",
                "spatial_resolution": "512 pixels/degree (~59.2 m/pixel at equator)",
                "crs": "Simple Cylindrical (Moon 2000 Mean Earth / Polar Axis DE421)",
                "longitude_convention": "0 to 360 East",
                "latitude_convention": "-90 to +90 North",
                "vertical_datum": "Reference Spheroid R = 1737.4 km",
                "elevation_units": "meters",
                "nodata_value": -32768.0,
                "file_format": "NPZ Cache from PDS3 JP2 Tile",
            }
            inst = cls(
                elevation_grid=data["elevation"],
                lat_min=float(data["lat_min"]),
                lat_max=float(data["lat_max"]),
                lon_min=float(data["lon_min"]),
                lon_max=float(data["lon_max"]),
                resolution_ppd=float(data.get("resolution_ppd", 512.0)),
                reference_radius_km=float(data.get("reference_radius_km", 1737.4)),
                nodata_value=float(data.get("nodata_value", -32768.0)),
                source_name="SLDEM2015_512_00N_30N_000_045",
                metadata=meta,
            )
            if use_cache:
                cls._INSTANCE = inst
            return inst

        raise FileNotFoundError(f"DEM dataset file not found at {buf_path}")

    @staticmethod
    def _resolve_path(path_str: str) -> Path:
        p = Path(path_str)
        if p.is_absolute() and p.exists():
            return p
        if p.exists():
            return p.resolve()
        try:
            curr_file = Path(__file__).resolve()
            for parent in curr_file.parents:
                cand = parent / p
                if cand.exists():
                    return cand.resolve()
        except Exception:
            pass
        return p

    def contains_coordinate(
        self,
        longitude: Union[float, np.ndarray],
        latitude: Union[float, np.ndarray],
    ) -> Union[bool, np.ndarray]:
        """Checks whether coordinates fall within the valid calibrated DEM domain."""
        is_scalar = np.isscalar(longitude) and np.isscalar(latitude)
        lon_arr = np.asarray(longitude, dtype=np.float64)
        lat_arr = np.asarray(latitude, dtype=np.float64)

        mask = (
            (lon_arr >= self.lon_min)
            & (lon_arr <= self.lon_max)
            & (lat_arr >= self.lat_min)
            & (lat_arr <= self.lat_max)
        )
        return bool(mask.item()) if is_scalar else mask

    def sample(
        self,
        longitude: Union[float, np.ndarray, List[float]],
        latitude: Union[float, np.ndarray, List[float]],
        method: str = "bilinear",
        raise_out_of_bounds: bool = False,
    ) -> Union[float, np.ndarray]:
        """Samples terrain elevation in meters relative to reference radius (1737.4 km).

        Args:
            longitude: Selenographic longitude(s) in degrees East.
            latitude: Selenographic latitude(s) in degrees North.
            method: Interpolation mode ('bilinear' or 'nearest').
            raise_out_of_bounds: If True, raises DEMOutOfBoundsError on out-of-domain coordinates.

        Returns:
            Elevation in meters. Returns np.nan for out-of-bounds coordinates if raise_out_of_bounds=False.
        """
        is_scalar = np.isscalar(longitude) and np.isscalar(latitude)
        lon_arr = np.asarray(longitude, dtype=np.float64)
        lat_arr = np.asarray(latitude, dtype=np.float64)

        if lon_arr.shape != lat_arr.shape:
            lon_arr, lat_arr = np.broadcast_arrays(lon_arr, lat_arr)

        orig_shape = lon_arr.shape
        flat_lon = lon_arr.ravel()
        flat_lat = lat_arr.ravel()

        in_domain = (
            (flat_lon >= self.lon_min)
            & (flat_lon <= self.lon_max)
            & (flat_lat >= self.lat_min)
            & (flat_lat <= self.lat_max)
        )

        if not np.all(in_domain):
            if raise_out_of_bounds:
                bad_idx = np.where(~in_domain)[0][0]
                raise DEMOutOfBoundsError(
                    f"Coordinate (lon={flat_lon[bad_idx]:.5f}, lat={flat_lat[bad_idx]:.5f}) is outside DEM domain: "
                    f"Lon=[{self.lon_min}, {self.lon_max}], Lat=[{self.lat_min}, {self.lat_max}]"
                )

        # Simple Cylindrical mapping:
        # line = (lat_max - lat) * resolution_ppd
        # sample = (lon - lon_min) * resolution_ppd
        f_line = (self.lat_max - flat_lat) * self.resolution_ppd
        f_samp = (flat_lon - self.lon_min) * self.resolution_ppd

        output = np.full(flat_lon.shape, np.nan, dtype=np.float32)

        valid_idx = np.where(in_domain)[0]
        if len(valid_idx) == 0:
            return float(np.nan) if is_scalar else output.reshape(orig_shape)

        v_lines = f_line[valid_idx]
        v_samps = f_samp[valid_idx]

        if method == "nearest":
            i_line = np.clip(np.round(v_lines).astype(int), 0, self.n_lines - 1)
            i_samp = np.clip(np.round(v_samps).astype(int), 0, self.n_samples - 1)
            vals = self.elevation[i_line, i_samp]
            nodata_mask = (vals == self.nodata_value) | np.isnan(vals)
            vals[nodata_mask] = np.nan
            output[valid_idx] = vals
        else:
            # Bilinear interpolation
            l0 = np.clip(np.floor(v_lines).astype(int), 0, self.n_lines - 1)
            l1 = np.clip(l0 + 1, 0, self.n_lines - 1)
            s0 = np.clip(np.floor(v_samps).astype(int), 0, self.n_samples - 1)
            s1 = np.clip(s0 + 1, 0, self.n_samples - 1)

            dl = v_lines - l0
            ds = v_samps - s0

            v00 = self.elevation[l0, s0]
            v01 = self.elevation[l0, s1]
            v10 = self.elevation[l1, s0]
            v11 = self.elevation[l1, s1]

            # Check no-data
            nodata_m = (
                (v00 == self.nodata_value)
                | (v01 == self.nodata_value)
                | (v10 == self.nodata_value)
                | (v11 == self.nodata_value)
            )

            interp_vals = (
                v00 * (1.0 - ds) * (1.0 - dl)
                + v01 * ds * (1.0 - dl)
                + v10 * (1.0 - ds) * dl
                + v11 * ds * dl
            )
            interp_vals[nodata_m] = np.nan
            output[valid_idx] = interp_vals

        if is_scalar:
            return float(output[0])
        return output.reshape(orig_shape)

    def sample_statistics(
        self,
        longitude: Union[float, np.ndarray, List[float]],
        latitude: Union[float, np.ndarray, List[float]],
    ) -> Dict[str, Any]:
        """Calculates elevation summary statistics over sampled coordinates."""
        vals = np.asarray(self.sample(longitude, latitude, method="bilinear", raise_out_of_bounds=False))
        flat_vals = vals.ravel()
        total_count = len(flat_vals)
        valid_mask = np.isfinite(flat_vals)
        valid_count = int(np.sum(valid_mask))
        nodata_count = total_count - valid_count

        valid_vals = flat_vals[valid_mask]
        if valid_count == 0:
            return {
                "total_points": total_count,
                "valid_count": 0,
                "nodata_count": total_count,
                "valid_percentage": 0.0,
                "nodata_percentage": 100.0,
                "min_elevation_m": None,
                "max_elevation_m": None,
                "mean_elevation_m": None,
                "median_elevation_m": None,
                "std_elevation_m": None,
            }

        return {
            "total_points": total_count,
            "valid_count": valid_count,
            "nodata_count": nodata_count,
            "valid_percentage": float(valid_count / total_count * 100.0),
            "nodata_percentage": float(nodata_count / total_count * 100.0),
            "min_elevation_m": float(np.min(valid_vals)),
            "max_elevation_m": float(np.max(valid_vals)),
            "mean_elevation_m": float(np.mean(valid_vals)),
            "median_elevation_m": float(np.median(valid_vals)),
            "std_elevation_m": float(np.std(valid_vals)),
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Returns structured metadata dictionary."""
        return {
            "source_name": self.source_name,
            "latitude_bounds": (self.lat_min, self.lat_max),
            "longitude_bounds": (self.lon_min, self.lon_max),
            "raster_dimensions": (self.n_lines, self.n_samples),
            "resolution_ppd": self.resolution_ppd,
            "spatial_resolution_m": float((np.pi * self.reference_radius_km * 1000.0 / 180.0) / self.resolution_ppd),
            "reference_radius_km": self.reference_radius_km,
            "nodata_value": self.nodata_value,
            **self.metadata,
        }
