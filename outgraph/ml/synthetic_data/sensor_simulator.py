"""Sensor Simulator for Lunar Multi-Modal Payloads (OHRC, TMC-2, IIRS).
Renders physically-grounded synthetic observations from digital elevation and mineral models.
Applies Hapke / Lommel-Seeliger lunar photometric models, sensor noise, PSF blur,
and spatial re-sampling. All observations are strictly labeled SYNTHETIC / DEMO DATA.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2
import scipy.ndimage as ndimage

from .terrain_generator import SyntheticLunarLandscape


@dataclass
class SimulatedObservation:
    observation_id: str
    sensor_type: str  # "OHRC", "TMC-2", "IIRS"
    image_data: np.ndarray  # uint8 [H, W] for single-band or [H, W, 3] for multi-band / RGB display
    raw_data: np.ndarray  # float32 calibrated reflectance or elevation
    spatial_resolution_m: float
    sun_azimuth_deg: float
    sun_elevation_deg: float
    incidence_angle_deg: float
    emission_angle_deg: float
    phase_angle_deg: float
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_synthetic: bool = True


class SensorSimulator:
    """Simulates realistic remote sensing observations for Chandrayaan-2 style payloads."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _compute_lunar_shading(
        self,
        elevation: np.ndarray,
        pixel_scale_m: float,
        sun_azimuth_deg: float,
        sun_elevation_deg: float,
        c_weight: float = 0.7,  # Lunar-Lambert weight parameter
    ) -> np.ndarray:
        """Computes Lunar-Lambert / Lommel-Seeliger hybrid photometric surface reflectance."""
        h, w = elevation.shape
        dy, dx = np.gradient(elevation, pixel_scale_m)

        # Surface normal vector [nx, ny, nz]
        # In image coords: x is right (East), y is down (South), z is up
        norm = np.sqrt(dx * dx + dy * dy + 1.0)
        nx = -dx / norm
        ny = -dy / norm
        nz = 1.0 / norm
     
        # Sun direction vector
        az_rad = np.radians(sun_azimuth_deg)
        el_rad = np.radians(sun_elevation_deg)
        # Assuming azimuth 0 is North (up/-y), 90 is East (+x)
        sx = np.sin(az_rad) * np.cos(el_rad)
        sy = -np.cos(az_rad) * np.cos(el_rad)
        sz = np.sin(el_rad)

        # Incidence cosine (cos i)
        cos_i = np.maximum(nx * sx + ny * sy + nz * sz, 0.0)

        # Emission cosine (cos e) for near-nadir viewing (viewing vector = [0, 0, 1])
        cos_e = np.maximum(nz, 1e-4)

        # Lommel-Seeliger term: cos_i / (cos_i + cos_e)
        ls_term = np.where(cos_i > 0, cos_i / (cos_i + cos_e), 0.0)

        # Lambert term: cos_i
        lambert_term = cos_i

        # Hybrid Lunar-Lambertian reflectance
        reflectance = (1.0 - c_weight) * ls_term + c_weight * lambert_term

        # Add shadow ray-casting approximation
        # If cos_i <= 0, completely in local slope shadow
        reflectance = np.where(cos_i <= 0.0, 0.02, reflectance)

        return reflectance.astype(np.float32)

    def simulate_ohrc(
        self,
        landscape: SyntheticLunarLandscape,
        observation_id: str = "OBS-OHRC-001",
        crop_box: Optional[Tuple[int, int, int, int]] = None,
        sun_azimuth_deg: float = 45.0,
        sun_elevation_deg: float = 25.0,
        target_size: int = 512,
        noise_level: float = 0.015,
    ) -> SimulatedObservation:
        """Simulates Optical High-Resolution Camera (OHRC).
        Features: High resolution (0.25-0.5m/px), sharp crater rims, boulder shadows, high-frequency texture.
        """
        # Select region of interest
        if crop_box is None:
            # Center region
            pad = (landscape.elevation_map.shape[0] - target_size) // 2
            crop_box = (pad, pad, pad + target_size, pad + target_size)

        y0, x0, y1, x1 = crop_box
        sub_dem = landscape.elevation_map[y0:y1, x0:x1]

        # Calculate high-detail photometric shading
        shading = self._compute_lunar_shading(
            sub_dem,
            pixel_scale_m=landscape.pixel_scale_m,
            sun_azimuth_deg=sun_azimuth_deg,
            sun_elevation_deg=sun_elevation_deg,
            c_weight=0.6,
        )

        # Add fine regolith texture (micro-craters / grain noise)
        texture = self.rng.normal(0, noise_level, shading.shape).astype(np.float32)
        img_float = np.clip(shading + texture, 0.0, 1.0)

        # Scale to 8-bit image
        img_uint8 = (img_float * 255.0).astype(np.uint8)

        # Geometric angles
        inc_angle = 90.0 - sun_elevation_deg
        em_angle = 2.0  # Near-nadir
        phase_angle = np.abs(inc_angle - em_angle)

        lat_span = (y1 - y0) * 0.0005
        lon_span = (x1 - x0) * 0.0005

        return SimulatedObservation(
            observation_id=observation_id,
            sensor_type="OHRC",
            image_data=img_uint8,
            raw_data=img_float,
            spatial_resolution_m=0.32,  # Sub-meter
            sun_azimuth_deg=sun_azimuth_deg,
            sun_elevation_deg=sun_elevation_deg,
            incidence_angle_deg=inc_angle,
            emission_angle_deg=em_angle,
            phase_angle_deg=phase_angle,
            lat_min=landscape.lat_center - lat_span / 2,
            lat_max=landscape.lat_center + lat_span / 2,
            lon_min=landscape.lon_center - lon_span / 2,
            lon_max=landscape.lon_center + lon_span / 2,
            metadata={
                "sensor_name": "Optical High Resolution Camera (OHRC)",
                "mission": "Chandrayaan-2 Payload Simulation",
                "spectral_band": "Panchromatic (450-900nm)",
                "snr_db": 42.5,
                "focal_length_mm": 1200.0,
                "pixel_pitch_um": 7.0,
                "exposure_time_ms": 3.2,
                "disclaimer": "SYNTHETIC / DEMO DATA - Physics-grounded simulation",
            },
        )

    def simulate_tmc2(
        self,
        landscape: SyntheticLunarLandscape,
        observation_id: str = "OBS-TMC2-001",
        crop_box: Optional[Tuple[int, int, int, int]] = None,
        sun_azimuth_deg: float = 135.0,  # Different solar angle
        sun_elevation_deg: float = 35.0,
        target_size: int = 512,
        scale_factor: float = 0.5,  # Slightly lower resolution / wider area representation
    ) -> SimulatedObservation:
        """Simulates Terrain Mapping Camera-2 (TMC-2).
        Features: Stereo DEM derivative, topography elevation rendering, smooth shading, 5m/px scale.
        """
        if crop_box is None:
            pad = (landscape.elevation_map.shape[0] - target_size) // 2
            crop_box = (pad, pad, pad + target_size, pad + target_size)

        y0, x0, y1, x1 = crop_box
        sub_dem = landscape.elevation_map[y0:y1, x0:x1]

        # Downsample and blur slightly to reflect ~5m/px TMC-2 resolution
        blurred_dem = ndimage.gaussian_filter(sub_dem, sigma=1.2)

        # TMC-2 Shading with different illumination
        shading = self._compute_lunar_shading(
            blurred_dem,
            pixel_scale_m=5.0,
            sun_azimuth_deg=sun_azimuth_deg,
            sun_elevation_deg=sun_elevation_deg,
            c_weight=0.75,
        )

        # Add modest sensor noise
        noise = self.rng.normal(0, 0.02, shading.shape).astype(np.float32)
        img_float = np.clip(shading + noise, 0.0, 1.0)
        img_uint8 = (img_float * 255.0).astype(np.uint8)

        inc_angle = 90.0 - sun_elevation_deg
        em_angle = 8.5
        phase_angle = np.abs(inc_angle - em_angle)

        lat_span = (y1 - y0) * 0.0005
        lon_span = (x1 - x0) * 0.0005

        return SimulatedObservation(
            observation_id=observation_id,
            sensor_type="TMC-2",
            image_data=img_uint8,
            raw_data=blurred_dem,
            spatial_resolution_m=5.0,
            sun_azimuth_deg=sun_azimuth_deg,
            sun_elevation_deg=sun_elevation_deg,
            incidence_angle_deg=inc_angle,
            emission_angle_deg=em_angle,
            phase_angle_deg=phase_angle,
            lat_min=landscape.lat_center - lat_span / 2,
            lat_max=landscape.lat_center + lat_span / 2,
            lon_min=landscape.lon_center - lon_span / 2,
            lon_max=landscape.lon_center + lon_span / 2,
            metadata={
                "sensor_name": "Terrain Mapping Camera-2 (TMC-2)",
                "mission": "Chandrayaan-2 Payload Simulation",
                "stereo_modes": ["Fore", "Nadir", "Aft"],
                "spectral_band": "Panchromatic (500-850nm)",
                "dem_vertical_precision_m": 3.0,
                "disclaimer": "SYNTHETIC / DEMO DATA - Physics-grounded simulation",
            },
        )

    def simulate_iirs(
        self,
        landscape: SyntheticLunarLandscape,
        observation_id: str = "OBS-IIRS-001",
        crop_box: Optional[Tuple[int, int, int, int]] = None,
        sun_azimuth_deg: float = 90.0,
        sun_elevation_deg: float = 40.0,
        target_size: int = 512,
    ) -> SimulatedObservation:
        """Simulates Imaging Infrared Spectrometer (IIRS).
        Features: Multi-channel SWIR mineral reflectance (pyroxene 1um/2um, plagioclase, olivine FeO).
        Visualized as a calibrated false-color RGB image.
        """
        if crop_box is None:
            pad = (landscape.elevation_map.shape[0] - target_size) // 2
            crop_box = (pad, pad, pad + target_size, pad + target_size)

        y0, x0, y1, x1 = crop_box
        minerals_sub = landscape.mineral_map[:, y0:y1, x0:x1]

        # Smooth to reflect ~20m/px IIRS spatial resolution
        band_r = ndimage.gaussian_filter(minerals_sub[1], sigma=2.0)  # Pyroxene (1.0 & 2.0 um absorption)
        band_g = ndimage.gaussian_filter(minerals_sub[0], sigma=2.0)  # Anorthosite/Plagioclase
        band_b = ndimage.gaussian_filter(minerals_sub[2], sigma=2.0)  # Olivine / FeO index

        # Create false-color RGB
        rgb_raw = np.stack([band_r, band_g, band_b], axis=-1)
        rgb_norm = np.clip((rgb_raw - rgb_raw.min()) / (rgb_raw.max() - rgb_raw.min() + 1e-6), 0.0, 1.0)
        img_uint8 = (rgb_norm * 255.0).astype(np.uint8)

        inc_angle = 90.0 - sun_elevation_deg
        em_angle = 0.5
        phase_angle = np.abs(inc_angle - em_angle)

        lat_span = (y1 - y0) * 0.0005
        lon_span = (x1 - x0) * 0.0005

        return SimulatedObservation(
            observation_id=observation_id,
            sensor_type="IIRS",
            image_data=img_uint8,
            raw_data=rgb_raw,
            spatial_resolution_m=20.0,
            sun_azimuth_deg=sun_azimuth_deg,
            sun_elevation_deg=sun_elevation_deg,
            incidence_angle_deg=inc_angle,
            emission_angle_deg=em_angle,
            phase_angle_deg=phase_angle,
            lat_min=landscape.lat_center - lat_span / 2,
            lat_max=landscape.lat_center + lat_span / 2,
            lon_min=landscape.lon_center - lon_span / 2,
            lon_max=landscape.lon_center + lon_span / 2,
            metadata={
                "sensor_name": "Imaging Infrared Spectrometer (IIRS)",
                "mission": "Chandrayaan-2 Payload Simulation",
                "spectral_range_um": "0.8 - 5.0 um (256 contiguous bands)",
                "spectral_sampling_nm": 16.5,
                "pyroxene_band_center_um": 0.95,
                "hydroxyl_water_band_um": 2.85,
                "disclaimer": "SYNTHETIC / DEMO DATA - Physics-grounded simulation",
            },
        )
