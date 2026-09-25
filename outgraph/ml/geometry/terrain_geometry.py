"""DEM-Aware Terrain Geometry Engine.

Extends the ISRO 2D GroundGrid coordinate system with physical Digital Elevation
Model (DEM) terrain heights (h) relative to the lunar reference spheroid (R = 1737.4 km).

Strictly distinguishes:
    1. Reference Datum Surface: (lon, lat, h = 0.0)
    2. Physical Terrain Surface: (lon, lat, h = DEM(lon, lat))

Scientific Guardrails:
    - Maintains GroundGrid immutability: underlying calibrated grids are never altered.
    - No-data and out-of-bounds DEM samples propagate explicitly as invalid (np.nan).
    - Vectorized operations preserve input tensor shapes.
    - Does NOT claim physical correspondence or photogrammetric triangulation.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

from .ground_grid import GroundGrid, GroundGridOutOfBoundsError, GroundGridError
from .dem_interface import DEMInterface, DEMOutOfBoundsError, DEMError


class TerrainGeometryError(GroundGridError):
    """Base exception for terrain geometry errors."""
    pass


class TerrainGeometry:
    """Combines calibrated GroundGrid with DEM elevation to produce 3D selenographic points."""

    def __init__(self, ground_grid: GroundGrid, dem: DEMInterface):
        """Initializes terrain geometry framework.

        Args:
            ground_grid: Calibrated ISRO GroundGrid instance.
            dem: Authoritative Lunar DEMInterface instance.
        """
        if not isinstance(ground_grid, GroundGrid):
            raise TypeError("ground_grid must be an instance of GroundGrid")
        if not isinstance(dem, DEMInterface):
            raise TypeError("dem must be an instance of DEMInterface")

        self.ground_grid = ground_grid
        self.dem = dem

    def pixel_to_terrain(
        self,
        pixel: Union[float, np.ndarray, List[float]],
        scan: Union[float, np.ndarray, List[float]],
        use_dem: bool = True,
        default_elevation: float = 0.0,
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Maps image pixel/scan coordinates to 3D selenographic coordinates (lon, lat, h).

        Args:
            pixel: Image sample coordinate(s).
            scan: Image line/scan coordinate(s).
            use_dem: If True, samples elevation from real DEM; if False, sets h = default_elevation (datum).
            default_elevation: Elevation in meters when use_dem=False (default 0.0).
            raise_out_of_bounds: If True, raises exception on out-of-domain coordinates.

        Returns:
            Tuple of (longitude_deg, latitude_deg, elevation_meters).
        """
        is_scalar = np.isscalar(pixel) and np.isscalar(scan)
        lons, lats = self.ground_grid.pixel_to_ground(pixel, scan, raise_out_of_bounds=raise_out_of_bounds)

        if not use_dem:
            if is_scalar:
                h_val = float(default_elevation) if np.isfinite(lons) and np.isfinite(lats) else float(np.nan)
                return float(lons), float(lats), h_val
            h_arr = np.full_like(lons, default_elevation, dtype=np.float32)
            invalid_m = np.isnan(lons) | np.isnan(lats)
            h_arr[invalid_m] = np.nan
            return lons, lats, h_arr

        # Sample from DEM
        elev = self.dem.sample(lons, lats, method="bilinear", raise_out_of_bounds=raise_out_of_bounds)

        if is_scalar:
            return float(lons), float(lats), float(elev)
        return lons, lats, elev

    def terrain_to_pixel(
        self,
        longitude: Union[float, np.ndarray, List[float]],
        latitude: Union[float, np.ndarray, List[float]],
        raise_out_of_bounds: bool = False,
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Maps geographic coordinates back to image pixel and scan coordinates."""
        return self.ground_grid.ground_to_pixel(longitude, latitude, raise_out_of_bounds=raise_out_of_bounds)

    def sample_transect(
        self,
        start_pixel: float,
        start_scan: float,
        end_pixel: float,
        end_scan: float,
        num_points: int = 50,
    ) -> Dict[str, np.ndarray]:
        """Samples a linear coordinate transect across the image plane."""
        pixels = np.linspace(start_pixel, end_pixel, num_points)
        scans = np.linspace(start_scan, end_scan, num_points)

        lons, lats, elevs = self.pixel_to_terrain(pixels, scans, use_dem=True)
        _, _, datum_elevs = self.pixel_to_terrain(pixels, scans, use_dem=False, default_elevation=0.0)

        return {
            "pixels": pixels,
            "scans": scans,
            "longitudes": lons,
            "latitudes": lats,
            "terrain_elevations_m": elevs,
            "datum_elevations_m": datum_elevs,
        }
