"""Sub-Pixel Registration Module.
Provides coarse-to-fine registration, dense warp, and sub-pixel Enhanced Correlation Coefficient (ECC) optimization.
"""
from .ecc_refinement import ECCRefiner, SubPixelResult
from .subpixel_engine import SubPixelRegistrationEngine, RegistrationExperimentResult

__all__ = [
    "ECCRefiner",
    "SubPixelResult",
    "SubPixelRegistrationEngine",
    "RegistrationExperimentResult",
]
