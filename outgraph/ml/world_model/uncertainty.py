"""Physical Uncertainty Propagation Engine for Lunar World Model.
Stage 4.4: Physics-Aware Uncertainty Modeling & Deterministic Propagation.

Supports:
- Scalar uncertainty
- Deterministic intervals / bounds [min, max]
- 2D covariance matrices (e.g. GroundGrid localization covariance)
- Qualitative scientific uncertainty ratings
- Explicit UNKNOWN representation without silent fabrication of confidence numbers.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
import math
import numpy as np
from pydantic import BaseModel, Field


class UncertaintyType(str, Enum):
    """Categorical type of uncertainty representation."""
    SCALAR = "SCALAR"
    INTERVAL = "INTERVAL"
    COVARIANCE = "COVARIANCE"
    QUALITATIVE = "QUALITATIVE"
    UNKNOWN = "UNKNOWN"


class PhysicalUncertainty(BaseModel):
    """Container for scientifically grounded uncertainty."""
    uncertainty_type: UncertaintyType = UncertaintyType.UNKNOWN
    scalar_value: Optional[float] = None
    interval_bounds: Optional[List[float]] = None  # [lower_bound, upper_bound]
    covariance_matrix: Optional[List[List[float]]] = None
    qualitative_label: Optional[str] = None
    unit: Optional[str] = None
    source: str = "UNKNOWN_SOURCE"
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"frozen": False}

    @classmethod
    def scalar(cls, value: float, unit: str, source: str, description: Optional[str] = None) -> "PhysicalUncertainty":
        return cls(
            uncertainty_type=UncertaintyType.SCALAR,
            scalar_value=value,
            unit=unit,
            source=source,
            description=description,
        )

    @classmethod
    def interval(cls, lower: float, upper: float, unit: str, source: str, description: Optional[str] = None) -> "PhysicalUncertainty":
        return cls(
            uncertainty_type=UncertaintyType.INTERVAL,
            interval_bounds=[float(lower), float(upper)],
            unit=unit,
            source=source,
            description=description,
        )

    @classmethod
    def covariance(cls, cov_matrix: List[List[float]], unit: str, source: str, description: Optional[str] = None) -> "PhysicalUncertainty":
        return cls(
            uncertainty_type=UncertaintyType.COVARIANCE,
            covariance_matrix=cov_matrix,
            unit=unit,
            source=source,
            description=description,
        )

    @classmethod
    def qualitative(cls, label: str, source: str, description: Optional[str] = None) -> "PhysicalUncertainty":
        return cls(
            uncertainty_type=UncertaintyType.QUALITATIVE,
            qualitative_label=label,
            source=source,
            description=description,
        )

    @classmethod
    def unknown(cls, source: str = "UNMEASURED", description: Optional[str] = None) -> "PhysicalUncertainty":
        return cls(
            uncertainty_type=UncertaintyType.UNKNOWN,
            source=source,
            description=description or "Uncertainty unquantified / unknown",
        )


class UncertaintyChain(BaseModel):
    """Complete traceable chain of uncertainty propagation."""
    source_uncertainty: PhysicalUncertainty
    geometry_uncertainty: Optional[PhysicalUncertainty] = None
    correspondence_uncertainty: Optional[PhysicalUncertainty] = None
    association_uncertainty: Optional[PhysicalUncertainty] = None
    hypothesis_uncertainty: Optional[PhysicalUncertainty] = None


class UncertaintyPropagator:
    """Propagates physical uncertainty through sensor, geometry, association, and belief stages."""

    @staticmethod
    def propagate_geometric_uncertainty(
        source_res_m: float,
        dem_res_m: float,
        corridor_width_m: float,
        sensor_type: str = "OHRC",
    ) -> PhysicalUncertainty:
        """Combines sensor GSD, DEM raster sampling limitations, and parallax corridor width

        into a deterministic spatial interval bound.
        """
        # Lower bound: minimal localization limit = sensor GSD
        lower_bound_m = source_res_m

        # Upper bound: quadrature sum of sensor GSD, DEM resolution limit, and parallax relief corridor
        upper_bound_m = math.sqrt(source_res_m**2 + dem_res_m**2 + corridor_width_m**2)

        return PhysicalUncertainty.interval(
            lower=round(lower_bound_m, 2),
            upper=round(upper_bound_m, 2),
            unit="meters",
            source=f"{sensor_type}_GEOMETRY_PARALLAX_PROPAGATION",
            description=f"Quadrature bound from sensor GSD ({source_res_m}m), DEM resolution ({dem_res_m}m), and parallax corridor ({corridor_width_m}m)",
        )

    @staticmethod
    def propagate_association_uncertainty(
        geom_uncertainty: PhysicalUncertainty,
        spatial_distance_m: float,
        spatial_tolerance_m: float,
    ) -> PhysicalUncertainty:
        """Propagates geometry uncertainty to entity association."""
        if geom_uncertainty.uncertainty_type == UncertaintyType.UNKNOWN:
            return PhysicalUncertainty.unknown(
                source="ENTITY_ASSOCIATION",
                description="Cannot propagate uncertainty from unknown geometry uncertainty",
            )

        if spatial_distance_m > spatial_tolerance_m:
            return PhysicalUncertainty.qualitative(
                label="REJECTED_OUT_OF_BOUNDS",
                source="ENTITY_SPATIAL_GATE",
                description=f"Spatial distance ({spatial_distance_m:.1f}m) exceeds tolerance ({spatial_tolerance_m:.1f}m)",
            )

        # In-bounds propagation
        if geom_uncertainty.interval_bounds:
            g_low, g_high = geom_uncertainty.interval_bounds
            # Additional association uncertainty induced by position offset
            assoc_low = g_low
            assoc_high = g_high + spatial_distance_m
            return PhysicalUncertainty.interval(
                lower=round(assoc_low, 2),
                upper=round(assoc_high, 2),
                unit="meters",
                source="ENTITY_ASSOCIATION_DISTANCE_OFFSET",
                description=f"Bounded spatial association uncertainty including {spatial_distance_m:.1f}m entity offset",
            )
        elif geom_uncertainty.scalar_value is not None:
            return PhysicalUncertainty.scalar(
                value=round(geom_uncertainty.scalar_value + spatial_distance_m, 2),
                unit=geom_uncertainty.unit or "meters",
                source="ENTITY_ASSOCIATION_DISTANCE_OFFSET",
            )

        return PhysicalUncertainty.qualitative(
            label="QUALITATIVE_IN_BOUNDS",
            source="ENTITY_ASSOCIATION",
        )

    @staticmethod
    def build_chain(
        source_unc: PhysicalUncertainty,
        geom_unc: Optional[PhysicalUncertainty] = None,
        corr_unc: Optional[PhysicalUncertainty] = None,
        assoc_unc: Optional[PhysicalUncertainty] = None,
        hyp_unc: Optional[PhysicalUncertainty] = None,
    ) -> UncertaintyChain:
        """Constructs a traceable uncertainty chain preserving the exact source at every node."""
        return UncertaintyChain(
            source_uncertainty=source_unc,
            geometry_uncertainty=geom_unc,
            correspondence_uncertainty=corr_unc,
            association_uncertainty=assoc_unc,
            hypothesis_uncertainty=hyp_unc,
        )
