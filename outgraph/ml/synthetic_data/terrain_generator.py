"""Synthetic Lunar Terrain & Digital Elevation Model (DEM) Generator.
Generates procedural lunar topographies with impact crater distributions (power-law),
boulders, ridges, fractal Brownian motion (fBm) elevation background, and mineral distribution maps.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import numpy as np
import scipy.ndimage as ndimage


@dataclass
class LunarCrater:
    x: float  # Pixel coordinate X
    y: float  # Pixel coordinate Y
    radius: float  # Pixel radius
    depth: float  # Depth in elevation units
    rim_height: float  # Rim elevation factor
    age_degradation: float  # 0.0 (fresh) to 1.0 (highly degraded)


@dataclass
class SyntheticLunarLandscape:
    elevation_map: np.ndarray  # 2D float32 array in meters
    mineral_map: np.ndarray  # 3D float32 array [C, H, W] (e.g. pyroxene, olivine, plagioclase)
    roughness_map: np.ndarray  # 2D float32 array
    slope_map: np.ndarray  # 2D float32 array in degrees
    aspect_map: np.ndarray  # 2D float32 array in radians [0, 2pi]
    craters: List[LunarCrater] = field(default_factory=list)
    seed: int = 42
    lat_center: float = -70.5
    lon_center: float = 22.8
    pixel_scale_m: float = 1.0  # 1 meter per pixel base resolution


class SyntheticTerrainGenerator:
    """Procedural generator for high-fidelity synthetic lunar DEMs and mineral layers."""

    def __init__(self, base_resolution: int = 1024, seed: int = 42):
        self.size = base_resolution
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def _generate_fbm_noise(
        self,
        shape: Tuple[int, int],
        octaves: int = 6,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
    ) -> np.ndarray:
        """Fractal Brownian motion noise for natural lunar topography."""
        h, w = shape
        noise = np.zeros((h, w), dtype=np.float32)
        amplitude = 1.0
        frequency = 1.0

        for _ in range(octaves):
            # Generate random smooth wave field using gaussian smoothed white noise
            sigma = max(1.0, (min(h, w) / (frequency * 8.0)))
            white = self.rng.standard_normal((h, w)).astype(np.float32)
            smoothed = ndimage.gaussian_filter(white, sigma=sigma)
            # Normalize step
            if smoothed.std() > 1e-6:
                smoothed = (smoothed - smoothed.mean()) / smoothed.std()
            noise += amplitude * smoothed
            amplitude *= persistence
            frequency *= lacunarity

        return noise

    def generate_crater_profile(
        self,
        grid_x: np.ndarray,
        grid_y: np.ndarray,
        crater: LunarCrater,
    ) -> np.ndarray:
        """Computes elevation offset for a single impact crater with parabolic bowl and raised rim."""
        dx = grid_x - crater.x
        dy = grid_y - crater.y
        dist = np.sqrt(dx * dx + dy * dy)
        r = np.maximum(dist / max(crater.radius, 1e-3), 1e-5)

        # Crater interior: parabolic excavation bowl
        interior = np.where(r <= 1.0, -crater.depth * (1.0 - (r ** 2)), 0.0)

        # Crater rim and continuous ejecta blanket: exponential decay
        rim_profile = crater.rim_height * np.exp(-((r - 1.0) ** 2) / (0.15 + 0.2 * crater.age_degradation))
        ejecta = np.where(r >= 0.85, rim_profile, 0.0)

        # Blend profile
        delta_h = interior + ejecta

        # Apply age degradation (softening)
        if crater.age_degradation > 0.1:
            delta_h *= (1.0 - 0.4 * crater.age_degradation)

        return delta_h.astype(np.float32)

    def compute_terrain_gradients(
        self, elevation: np.ndarray, pixel_scale_m: float
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Calculates slope (degrees), aspect (radians), and roughness (std of normal vectors)."""
        dy, dx = np.gradient(elevation, pixel_scale_m)
        slope_rad = np.arctan(np.sqrt(dx * dx + dy * dy))
        slope_deg = np.degrees(slope_rad).astype(np.float32)

        # Aspect: clockwise from North (0 is North)
        aspect_rad = (np.arctan2(-dx, dy) + 2 * np.pi) % (2 * np.pi)

        # Local terrain roughness (std of slopes in 5x5 window)
        roughness = ndimage.generic_filter(slope_deg, np.std, size=5).astype(np.float32)

        return slope_deg, aspect_rad.astype(np.float32), roughness

    def generate_landscape(
        self,
        lat_center: float = -70.5,
        lon_center: float = 22.8,
        num_craters: int = 40,
        num_boulders: int = 120,
    ) -> SyntheticLunarLandscape:
        """Generates a complete SyntheticLunarLandscape."""
        # 1. Base topography (fBm highland/mare relief)
        base_fbm = self._generate_fbm_noise((self.size, self.size), octaves=7, persistence=0.52)
        elevation = (base_fbm * 85.0).astype(np.float32)  # +/- 150m regional relief

        # Coordinate grids
        y_coords, x_coords = np.mgrid[0:self.size, 0:self.size]

        # 2. Add impact crater population (Power-law distribution)
        craters: List[LunarCrater] = []
        # Main prominent landmark craters
        prominent_craters = [
            LunarCrater(x=self.size * 0.42, y=self.size * 0.38, radius=85.0, depth=45.0, rim_height=18.0, age_degradation=0.15),
            LunarCrater(x=self.size * 0.72, y=self.size * 0.65, radius=55.0, depth=28.0, rim_height=11.0, age_degradation=0.25),
            LunarCrater(x=self.size * 0.25, y=self.size * 0.75, radius=40.0, depth=18.0, rim_height=8.0, age_degradation=0.40),
            LunarCrater(x=self.size * 0.60, y=self.size * 0.20, radius=32.0, depth=14.0, rim_height=6.0, age_degradation=0.20),
        ]
        craters.extend(prominent_craters)

        # Power-law small crater field
        for _ in range(num_craters):
            r = float(self.rng.power(0.35) * 25.0 + 3.0)
            cx = float(self.rng.uniform(10, self.size - 10))
            cy = float(self.rng.uniform(10, self.size - 10))
            depth = r * float(self.rng.uniform(0.18, 0.28))
            rim = depth * float(self.rng.uniform(0.2, 0.4))
            age = float(self.rng.uniform(0.05, 0.7))
            craters.append(LunarCrater(x=cx, y=cy, radius=r, depth=depth, rim_height=rim, age_degradation=age))

        # Apply craters to elevation map
        for c in craters:
            # Bounding box optimization
            pad = int(c.radius * 2.5) + 5
            x0, x1 = max(0, int(c.x - pad)), min(self.size, int(c.x + pad))
            y0, y1 = max(0, int(c.y - pad)), min(self.size, int(c.y + pad))

            if x1 > x0 and y1 > y0:
                sub_gx = x_coords[y0:y1, x0:x1]
                sub_gy = y_coords[y0:y1, x0:x1]
                prof = self.generate_crater_profile(sub_gx, sub_gy, c)
                elevation[y0:y1, x0:x1] += prof

        # 3. Add boulder clusters around fresh crater rims
        for _ in range(num_boulders):
            # Cluster near crater 0 or 1
            parent = self.rng.choice(prominent_craters)
            angle = self.rng.uniform(0, 2 * np.pi)
            dist = parent.radius * self.rng.uniform(0.9, 1.8)
            bx = int(np.clip(parent.x + dist * np.cos(angle), 5, self.size - 6))
            by = int(np.clip(parent.y + dist * np.sin(angle), 5, self.size - 6))
            b_height = float(self.rng.uniform(1.2, 4.5))
            elevation[by - 1 : by + 2, bx - 1 : bx + 2] += b_height

        # 4. Generate Mineral Composition Map [3 channels: Plagioclase/Anorthosite, Pyroxene, Olivine/FeO]
        # Inverted relative to crater interiors (fresh excavated basaltic / anorthositic material)
        minerals = np.zeros((3, self.size, self.size), dtype=np.float32)
        # Channel 0: Anorthosite (highland background)
        minerals[0] = 0.65 + 0.15 * ndimage.gaussian_filter(self.rng.standard_normal((self.size, self.size)), 20)
        # Channel 1: Clinopyroxene / Orthopyroxene (impact melts and crater centers)
        minerals[1] = 0.20 + 0.10 * ndimage.gaussian_filter(self.rng.standard_normal((self.size, self.size)), 15)
        # Channel 2: Olivine / FeO absorption index
        minerals[2] = 0.15 + 0.08 * ndimage.gaussian_filter(self.rng.standard_normal((self.size, self.size)), 10)

        # Enhance fresh crater mineral absorption signatures
        for c in craters[:5]:
            dist_sq = (x_coords - c.x) ** 2 + (y_coords - c.y) ** 2
            mask = np.exp(-dist_sq / (2.0 * (c.radius * 0.9) ** 2))
            minerals[1] += 0.25 * mask.astype(np.float32)
            minerals[0] -= 0.15 * mask.astype(np.float32)

        minerals = np.clip(minerals, 0.0, 1.0)

        # 5. Compute slope, aspect, roughness
        slope, aspect, roughness = self.compute_terrain_gradients(elevation, pixel_scale_m=1.0)

        return SyntheticLunarLandscape(
            elevation_map=elevation,
            mineral_map=minerals,
            roughness_map=roughness,
            slope_map=slope,
            aspect_map=aspect,
            craters=craters,
            seed=self.seed,
            lat_center=lat_center,
            lon_center=lon_center,
            pixel_scale_m=1.0,
        )
