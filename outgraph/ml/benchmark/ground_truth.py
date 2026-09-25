"""Ground Truth Hierarchy for Real Lunar Data & Synthetic Controls.

Levels:
  LEVEL_1: Georeferenced Overlap (reliable spatial lat/lon bounds overlap)
  LEVEL_2: Independent Geometric Reference (independent DEM/projection)
  LEVEL_3: Manually Verified Feature Correspondence (human verified)
  LEVEL_4: Synthetic Controlled Transform (synthetic benchmark control - NEVER real data!)
  UNKNOWN: Unestablished / missing ground truth
"""

from enum import Enum
from typing import Optional, Dict, Any
from ..data.models import LunarProduct, ValueStatus


class GroundTruthLevel(int, Enum):
    UNKNOWN = 0
    LEVEL_1_GEOREFERENCED = 1
    LEVEL_2_INDEPENDENT_DEM = 2
    LEVEL_3_MANUALLY_VERIFIED = 3
    LEVEL_4_SYNTHETIC_CONTROL = 4

    def to_string(self) -> str:
        names = {
            0: "LEVEL_UNKNOWN",
            1: "LEVEL_1_GEOREFERENCED_OVERLAP",
            2: "LEVEL_2_INDEPENDENT_GEOMETRIC_REFERENCE",
            3: "LEVEL_3_MANUALLY_VERIFIED",
            4: "LEVEL_4_SYNTHETIC_CONTROLLED_TRANSFORM",
        }
        return names.get(self.value, "LEVEL_UNKNOWN")


def evaluate_ground_truth_level(
    source_product: LunarProduct,
    target_product: LunarProduct,
    explicit_level: Optional[GroundTruthLevel] = None,
) -> GroundTruthLevel:
    """Evaluates ground truth hierarchy level cleanly based on data model and origin.
    CRITICAL: Synthetic controls are strictly Level 4 and can NEVER be reported as Level 1-3.
    """
    # If explicitly specified (e.g. human verified or synthetic control pair)
    if explicit_level is not None:
        if (source_product.is_synthetic or target_product.is_synthetic) and explicit_level != GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL:
            # Force Level 4 if any product is synthetic! Never claim real ground truth for synthetic.
            return GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL
        return explicit_level

    # Check if synthetic
    if source_product.is_synthetic or target_product.is_synthetic:
        return GroundTruthLevel.LEVEL_4_SYNTHETIC_CONTROL

    # Check if both have KNOWN geographic bounds
    src_gb = source_product.metadata.geographic_bounds
    tgt_gb = target_product.metadata.geographic_bounds

    if src_gb.status == ValueStatus.KNOWN and tgt_gb.status == ValueStatus.KNOWN:
        if (
            src_gb.lat_min is not None
            and src_gb.lat_max is not None
            and src_gb.lon_min is not None
            and src_gb.lon_max is not None
            and tgt_gb.lat_min is not None
            and tgt_gb.lat_max is not None
            and tgt_gb.lon_min is not None
            and tgt_gb.lon_max is not None
        ):
            # Check bounding box intersection
            lat_overlap = (src_gb.lat_min <= tgt_gb.lat_max) and (src_gb.lat_max >= tgt_gb.lat_min)
            lon_overlap = (src_gb.lon_min <= tgt_gb.lon_max) and (src_gb.lon_max >= tgt_gb.lon_min)
            if lat_overlap and lon_overlap:
                return GroundTruthLevel.LEVEL_1_GEOREFERENCED

    return GroundTruthLevel.UNKNOWN
