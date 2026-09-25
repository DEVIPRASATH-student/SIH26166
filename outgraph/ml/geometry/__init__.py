"""LunarSynapse Geometry and Coordinate Systems Package."""

from .ground_grid import GroundGrid, GroundGridError, GroundGridValidationError, GroundGridOutOfBoundsError
from .grid_projection import GridProjector, GridProjectionError
from .dem_interface import DEMInterface, DEMError, DEMOutOfBoundsError
from .terrain_geometry import TerrainGeometry, TerrainGeometryError
from .parallax_model import (
    ParallaxModel,
    ParallaxModelError,
    SensorParallaxParams,
    OHRC_PARALLAX_PARAMS,
    TMC2_PARALLAX_PARAMS,
)
from .target_corridor import (
    TargetCorridorCalculator,
    CorridorResult,
    TargetCorridorError,
)

__all__ = [
    "GroundGrid",
    "GroundGridError",
    "GroundGridValidationError",
    "GroundGridOutOfBoundsError",
    "GridProjector",
    "GridProjectionError",
    "DEMInterface",
    "DEMError",
    "DEMOutOfBoundsError",
    "TerrainGeometry",
    "TerrainGeometryError",
    "ParallaxModel",
    "ParallaxModelError",
    "SensorParallaxParams",
    "OHRC_PARALLAX_PARAMS",
    "TMC2_PARALLAX_PARAMS",
    "TargetCorridorCalculator",
    "CorridorResult",
    "TargetCorridorError",
]





