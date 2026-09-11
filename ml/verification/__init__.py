"""Physics Verification Module.
Implements multi-physics constraints: Geometry, Solar Illumination, Terrain/DEM Gradients,
Scale Consistency, and Spatial Distribution Entropy.
"""
from .geometry import GeometricVerifier, GeometryVerificationResult
from .illumination import IlluminationVerifier, IlluminationVerificationResult
from .terrain import TerrainVerifier, TerrainVerificationResult
from .scale_spatial import ScaleSpatialVerifier, ScaleSpatialResult
from .physics_engine import PhysicsVerificationEngine, PhysicsEvidenceProfile

__all__ = [
    "GeometricVerifier",
    "GeometryVerificationResult",
    "IlluminationVerifier",
    "IlluminationVerificationResult",
    "TerrainVerifier",
    "TerrainVerificationResult",
    "ScaleSpatialVerifier",
    "ScaleSpatialResult",
    "PhysicsVerificationEngine",
    "PhysicsEvidenceProfile",
]
