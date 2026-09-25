"""Sensor-Aware Preprocessing Interface.
Provides clean extension points for radiometric normalization, intensity normalization,
NoData masking, band selection, and geometric preparation.
Does NOT automatically apply destructive transformations to real scientific products.
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2

from ..models import LunarProduct, ProvenanceRecord
from ..provenance.tracker import ProvenanceTracker


class PreprocessingStep:
    """Represents a single modular preprocessing operation."""

    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params


class SensorAwarePreprocessor:
    """Sensor-aware preprocessing interface providing clean extension points."""

    @staticmethod
    def mask_nodata(product: LunarProduct) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Extracts raster array and creates NoData binary mask if nodata_value is defined."""
        arr = product.raster_data
        if arr is None:
            return np.zeros((0, 0), dtype=np.uint8), None

        nodata_val = product.metadata.nodata_value
        if nodata_val is not None:
            mask = (arr != nodata_val)
        else:
            mask = None
        return arr, mask

    @staticmethod
    def extract_correspondence_ready_view(
        product: LunarProduct,
        selected_band: int = 0,
        max_dimension: int = 2048,
    ) -> Tuple[np.ndarray, LunarProduct]:
        """Prepares a non-destructive 2D grayscale view suitable for feature matchers,
        retaining the original multi-band LunarProduct intact.
        """
        raw_band = product.get_band(selected_band)
        if raw_band is None:
            raise ValueError(f"Band {selected_band} not available in product {product.product_id}")

        # For large full-scene strip rasters (e.g. 78k x 12k or 214k x 4k), subsample view for matcher
        max_dim = max(raw_band.shape[:2])
        if max_dim > max_dimension:
            step = int(np.ceil(max_dim / max_dimension))
            working_band = raw_band[::step, ::step]
        else:
            working_band = raw_band

        # Non-destructive 8-bit visual view conversion for SIFT/ORB if uint16/float32
        if working_band.dtype == np.uint8:
            view_2d = np.array(working_band, copy=True)
        elif np.issubdtype(working_band.dtype, np.floating):
            # Scale min-max safely ignoring NaN/Inf
            valid_mask = np.isfinite(working_band)
            if valid_mask.any():
                v_min, v_max = float(working_band[valid_mask].min()), float(working_band[valid_mask].max())
                if v_max > v_min:
                    scaled = (working_band - v_min) / (v_max - v_min) * 255.0
                    view_2d = np.clip(scaled, 0, 255).astype(np.uint8)
                else:
                    view_2d = np.zeros_like(working_band, dtype=np.uint8)
            else:
                view_2d = np.zeros_like(working_band, dtype=np.uint8)
        elif working_band.dtype in [np.uint16, np.dtype("<u2"), np.dtype(">u2")]:
            v_min, v_max = float(working_band.min()), float(working_band.max())
            if v_max > v_min:
                scaled = (working_band.astype(np.float32) - v_min) / (v_max - v_min) * 255.0
                view_2d = np.clip(scaled, 0, 255).astype(np.uint8)
            else:
                view_2d = np.zeros(working_band.shape, dtype=np.uint8)
        else:
            view_2d = cv2.normalize(np.array(working_band), None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Log provenance step on product
        ProvenanceTracker.record_transformation(
            product.provenance,
            operation_name="CORRESPONDENCE_VIEW_EXTRACTION",
            parameters={"selected_band": selected_band, "source_dtype": str(raw_band.dtype), "view_shape": list(view_2d.shape)},
            description="Created non-destructive 8-bit visualization view for correspondence matchers",
        )

        return view_2d, product
