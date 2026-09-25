"""Elevation-Dependent Parallax and Relief Displacement Model.

Models how local lunar terrain elevation (h) relative to the reference spheroid
(R = 1737.4 km) shifts observed feature coordinates relative to the 2D reference datum.

Mathematical Formulation:
    For a pushbroom camera at spacecraft altitude H above the surface:
    Cross-track look angle for sample x:
        tan(theta_ct(x)) = (x - x_center) * GSD / (H * 1000.0)

    At terrain elevation h (meters) relative to datum (h_0 = 0.0):
    Horizontal ground relief displacement:
        delta_ground(h, x) = -h * tan(theta_look(x))
    
    Cross-track pixel displacement:
        delta_pixel(h, x) = delta_ground / GSD = - (h / (H * 1000.0)) * (x - x_center)

Properties:
    1. Zero-Displacement Datum: h = 0.0 ==> delta = 0.0 (exact reference datum preservation).
    2. Nadir Invariance: x = x_center ==> theta = 0.0 ==> delta = 0.0.
    3. Physical Directionality:
       - Depressions (h < 0, e.g. lunar mare) displace outward away from nadir.
       - Elevated terrain (h > 0, e.g. crater rims) displace inward toward nadir.
    4. Bounded Magnitude: For H ~ 100 km, GSD ~ 6 m, h ~ -2 km:
       Max horizontal displacement <= 300 meters (~50 TMC-2 pixels).

Scientific Assumptions & Guardrails:
    - Assumes near-nadir pushbroom linear CCD imaging geometry.
    - Uses verified spacecraft altitudes from ISRO PDS metadata (OHRC: 102.71 km, TMC-2: 121.43 km).
    - Does NOT fabricate unvalidated high-order spacecraft attitude jitter.
    - Does NOT claim full photogrammetric bundle-adjusted precision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, Union, Any, List
import numpy as np

from .ground_grid import GroundGridError


class ParallaxModelError(GroundGridError):
    """Base exception for parallax model errors."""
    pass


@dataclass(frozen=True)
class SensorParallaxParams:
    """Sensor optical and orbital parameters for parallax modeling."""
    sensor_name: str
    spacecraft_altitude_km: float
    ground_sampling_distance_m: float
    total_samples: int
    center_sample: float
    nominal_emission_angle_deg: float = 0.0  # Near-nadir
    focal_length_mm: Optional[float] = None
    pixel_pitch_um: Optional[float] = None


OHRC_PARALLAX_PARAMS = SensorParallaxParams(
    sensor_name="OHRC",
    spacecraft_altitude_km=102.71,
    ground_sampling_distance_m=0.25,
    total_samples=12000,
    center_sample=5999.5,
    nominal_emission_angle_deg=0.0,
    focal_length_mm=4000.0,
    pixel_pitch_um=7.0,
)

TMC2_PARALLAX_PARAMS = SensorParallaxParams(
    sensor_name="TMC-2",
    spacecraft_altitude_km=121.43,
    ground_sampling_distance_m=6.0,
    total_samples=4000,
    center_sample=1999.5,
    nominal_emission_angle_deg=0.0,
    focal_length_mm=1000.0,
    pixel_pitch_um=10.0,
)


class ParallaxModel:
    """Computes elevation-dependent relief displacement for pushbroom imaging sensors."""

    def __init__(self, params: SensorParallaxParams, moon_radius_km: float = 1737.4):
        """Initializes parallax model.

        Args:
            params: SensorParallaxParams configuration.
            moon_radius_km: Lunar reference sphere radius (default 1737.4 km).
        """
        self.params = params
        self.moon_radius_km = float(moon_radius_km)
        self.altitude_m = params.spacecraft_altitude_km * 1000.0
        self.gsd = params.ground_sampling_distance_m
        self.x_center = params.center_sample

    def compute_look_angle(
        self,
        pixel_sample: Union[float, np.ndarray, List[float]],
    ) -> Union[float, np.ndarray]:
        """Calculates cross-track look angle (radians) as a function of sample coordinate."""
        is_scalar = np.isscalar(pixel_sample)
        p = np.asarray(pixel_sample, dtype=np.float64)

        # Off-center ground distance in meters
        dx_m = (p - self.x_center) * self.gsd
        # tan(theta) = dx / H
        tan_theta = dx_m / self.altitude_m
        theta = np.arctan(tan_theta)

        return float(theta.item()) if is_scalar else theta

    def compute_ground_displacement(
        self,
        elevation_m: Union[float, np.ndarray, List[float]],
        pixel_sample: Union[float, np.ndarray, List[float]],
    ) -> Dict[str, Union[float, np.ndarray]]:
        """Calculates horizontal ground relief displacement vector caused by elevation h.

        Args:
            elevation_m: Terrain elevation in meters relative to reference sphere (h = 0).
            pixel_sample: Sensor sample/column coordinate(s).

        Returns:
            Dictionary with displacement_meters, cross_track_displacement_m,
            and look_angle_deg.
        """
        is_scalar = np.isscalar(elevation_m) and np.isscalar(pixel_sample)
        h = np.asarray(elevation_m, dtype=np.float64)
        p = np.asarray(pixel_sample, dtype=np.float64)

        if h.shape != p.shape:
            h, p = np.broadcast_arrays(h, p)

        # Look angle across swath
        theta_rad = self.compute_look_angle(p)
        tan_theta = np.tan(theta_rad)

        # Ground displacement: delta = -h * tan(theta)
        delta_m = -h * tan_theta

        # Invalidate when inputs are non-finite
        invalid = np.isnan(h) | np.isnan(p)
        delta_m = np.where(invalid, np.nan, delta_m)

        if is_scalar:
            return {
                "cross_track_displacement_m": float(delta_m.item()),
                "displacement_magnitude_m": float(np.abs(delta_m).item()),
                "look_angle_deg": float(np.degrees(theta_rad).item()),
            }

        return {
            "cross_track_displacement_m": delta_m,
            "displacement_magnitude_m": np.abs(delta_m),
            "look_angle_deg": np.degrees(theta_rad),
        }

    def compute_pixel_displacement(
        self,
        elevation_m: Union[float, np.ndarray, List[float]],
        pixel_sample: Union[float, np.ndarray, List[float]],
    ) -> Union[float, np.ndarray]:
        """Calculates displacement in sensor sample/pixel units: delta_pixel = delta_ground / GSD."""
        disp = self.compute_ground_displacement(elevation_m, pixel_sample)
        dx_m = disp["cross_track_displacement_m"]
        dp = dx_m / self.gsd
        if np.isscalar(dp):
            return float(dp)
        return dp

    def apply_parallax_correction(
        self,
        longitude: Union[float, np.ndarray, List[float]],
        latitude: Union[float, np.ndarray, List[float]],
        elevation_m: Union[float, np.ndarray, List[float]],
        pixel_sample: Union[float, np.ndarray, List[float]],
        ground_track_heading_deg: float = 0.0,  # 0 deg = Northbound polar orbit
    ) -> Tuple[Union[float, np.ndarray], Union[float, np.ndarray]]:
        """Applies physical relief displacement to reference selenographic coordinates.

        Args:
            longitude: Selenographic longitude on reference datum (deg East).
            latitude: Selenographic latitude on reference datum (deg North).
            elevation_m: Terrain elevation in meters (h).
            pixel_sample: Sensor sample/column coordinate.
            ground_track_heading_deg: Orbit ground track heading (0 deg = North, 90 deg = East).

        Returns:
            Tuple of (corrected_longitude, corrected_latitude).
        """
        is_scalar = np.isscalar(longitude) and np.isscalar(latitude)
        lon = np.asarray(longitude, dtype=np.float64)
        lat = np.asarray(latitude, dtype=np.float64)

        disp = self.compute_ground_displacement(elevation_m, pixel_sample)
        dx_cross = disp["cross_track_displacement_m"]

        # Cross-track is perpendicular to flight direction (heading + 90 deg)
        cross_azimuth_rad = np.radians(ground_track_heading_deg + 90.0)

        # Ground displacement components
        d_east_m = dx_cross * np.sin(cross_azimuth_rad)
        d_north_m = dx_cross * np.cos(cross_azimuth_rad)

        r_m = self.moon_radius_km * 1000.0
        rad_to_deg = 180.0 / np.pi

        d_lat_deg = (d_north_m / r_m) * rad_to_deg
        d_lon_deg = (d_east_m / (r_m * np.cos(np.radians(lat)))) * rad_to_deg

        lon_corr = lon + d_lon_deg
        lat_corr = lat + d_lat_deg

        if is_scalar:
            return float(lon_corr.item()), float(lat_corr.item())
        return lon_corr, lat_corr

    def get_max_possible_displacement(self, max_elevation_abs_m: float = 3000.0) -> Dict[str, float]:
        """Calculates theoretical maximum parallax displacement across full field of view."""
        max_sample = float(self.params.total_samples - 1)
        disp = self.compute_ground_displacement(max_elevation_abs_m, max_sample)
        max_ground_m = float(disp["displacement_magnitude_m"])
        max_pix = max_ground_m / self.gsd

        return {
            "max_elevation_abs_m": float(max_elevation_abs_m),
            "max_look_angle_deg": float(np.abs(disp["look_angle_deg"])),
            "max_ground_displacement_m": max_ground_m,
            "max_pixel_displacement": max_pix,
        }
