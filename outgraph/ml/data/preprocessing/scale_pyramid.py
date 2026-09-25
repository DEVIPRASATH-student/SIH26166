"""Scale Pyramid Generation & Memory-Safe Downsampling Engine.

Supports scientifically defensible multi-scale image pyramids for high-resolution lunar imagery
(e.g., Chandrayaan-2 OHRC at 0.26 m/px downsampled toward TMC-2 at 6.07 m/px).

Guarantees:
- Original source datasets are NEVER overwritten.
- All derived products are marked with DERIVED_FROM_REAL_DATA = TRUE.
- GSD, solar geometry, and geographic bounds are preserved.
"""

import os
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import cv2
import logging

from ..models import LunarProduct, ProductMetadata, ProvenanceRecord, ValueStatus, ValidationResult
from ..provenance.tracker import ProvenanceTracker

logger = logging.getLogger("LunarSynapse.ML.ScalePyramid")


@dataclass
class PyramidLevel:
    level_index: int
    name: str
    scale_factor: float  # Downsampling factor relative to level 0 (e.g. 1.0, 2.0, 4.0, 8.0, 16.0, 23.346)
    effective_gsd_m: float  # Physical ground sampling distance in meters/pixel
    lines: int
    samples: int
    resampling_method: str  # e.g. "anti_aliased_area_averaging"
    derived_image_path: str
    derived_product: LunarProduct

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level_index": self.level_index,
            "name": self.name,
            "scale_factor": round(self.scale_factor, 5),
            "effective_gsd_m": round(self.effective_gsd_m, 4),
            "dimensions": f"{self.lines}x{self.samples}",
            "resampling_method": self.resampling_method,
            "derived_image_path": self.derived_image_path,
        }


def compute_scale_ratio(source_gsd: float, target_gsd: float) -> float:
    """Computes exact physical GSD scale ratio: target_gsd / source_gsd."""
    if source_gsd <= 0.0 or target_gsd <= 0.0:
        raise ValueError(f"GSD values must be positive. Got source_gsd={source_gsd}, target_gsd={target_gsd}")
    return float(target_gsd / source_gsd)


class ScalePyramidGenerator:
    """Generates scientifically defensible anti-aliased image pyramids for lunar imagery."""

    def __init__(self, output_dir: str = "data/derived/scale_normalized"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_pyramid(
        self,
        product: LunarProduct,
        target_gsd_m: float = 6.07,
        custom_scale_factors: Optional[List[float]] = None,
    ) -> List[PyramidLevel]:
        """Generates multi-scale pyramid levels for input lunar product.

        Standard levels for OHRC (0.26 m/px) vs TMC-2 (6.07 m/px):
        - Level 0: 1.0x (Original 0.26 m/px)
        - Level 1: 2.0x (~0.52 m/px)
        - Level 2: 4.0x (~1.04 m/px)
        - Level 3: 8.0x (~2.08 m/px)
        - Level 4: 16.0x (~4.16 m/px)
        - Level 5: scale_ratio (~6.07 m/px, TMC-2 equivalent scale)
        """
        source_gsd = product.metadata.gsd_m
        if source_gsd is None or source_gsd <= 0:
            raise ValueError(f"Product {product.product_id} has invalid or missing GSD.")

        exact_tmc_scale = compute_scale_ratio(source_gsd, target_gsd_m)

        if custom_scale_factors is None:
            # Multi-scale factors
            scale_factors = [1.0, 2.0, 4.0, 8.0, 16.0, exact_tmc_scale]
        else:
            scale_factors = custom_scale_factors

        pyramid_levels: List[PyramidLevel] = []

        raw_raster = product.raster_data
        if raw_raster is None:
            raise ValueError(f"Product {product.product_id} has no raster data loaded.")

        h_orig, w_orig = raw_raster.shape[:2]

        for idx, sf in enumerate(scale_factors):
            level_name = f"Level_{idx}" if sf != exact_tmc_scale else f"Level_{idx}_TMC_Equivalent"
            eff_gsd = source_gsd * sf

            if sf == 1.0:
                # Level 0 is original (unmodified)
                p_level = PyramidLevel(
                    level_index=idx,
                    name="Level_0_Original",
                    scale_factor=1.0,
                    effective_gsd_m=source_gsd,
                    lines=h_orig,
                    samples=w_orig,
                    resampling_method="none_original",
                    derived_image_path=str(product.file_path),
                    derived_product=product,
                )
                pyramid_levels.append(p_level)
                continue

            # Compute new target dimensions
            new_w = max(1, int(round(w_orig / sf)))
            new_h = max(1, int(round(h_orig / sf)))

            # Anti-aliased downsampling (Gaussian pre-filter + INTER_AREA)
            downsampled_raster = self._downsample_memory_safe(raw_raster, target_size=(new_w, new_h), scale_factor=sf)

            # Save derived image raster safely
            out_filename = f"{product.metadata.product_id}_scale_{sf:.2f}x.png"
            out_path = os.path.join(self.output_dir, out_filename)

            # Convert to uint8 for derived visualization/matching
            if downsampled_raster.dtype == np.uint8:
                img_to_save = downsampled_raster
            else:
                img_to_save = cv2.normalize(downsampled_raster, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

            cv2.imwrite(out_path, img_to_save)

            # Create derived LunarProduct metadata
            derived_meta = ProductMetadata(
                product_id=f"{product.metadata.product_id}_LEVEL_{idx}",
                mission=product.metadata.mission,
                instrument=product.metadata.instrument,
                product_type="Derived Downsampled Raster",
                processing_level=product.metadata.processing_level,
                acquisition_timestamp=product.metadata.acquisition_timestamp,
                lines=new_h,
                samples=new_w,
                num_bands=product.metadata.num_bands,
                data_type=str(img_to_save.dtype),
                nodata_value=product.metadata.nodata_value,
                gsd_m=eff_gsd,
                geographic_bounds=product.metadata.geographic_bounds,
                solar_illumination=product.metadata.solar_illumination,
                viewing_geometry=product.metadata.viewing_geometry,
                value_statuses=dict(product.metadata.value_statuses),
                raw_metadata=dict(product.metadata.raw_metadata),
            )
            derived_meta.value_statuses["gsd_m"] = ValueStatus.KNOWN

            # Provenance record marking DERIVED_FROM_REAL_DATA = TRUE
            prov = ProvenanceRecord(
                source_name=f"Derived from {product.provenance.source_name}",
                original_filename=os.path.basename(out_path),
                product_id=derived_meta.product_id,
                sha256_checksum=ProvenanceTracker.calculate_sha256(Path(out_path)),
                metadata_extraction_status="SUCCESS",
            )
            ProvenanceTracker.record_transformation(
                prov,
                operation_name="SCALE_NORMALIZATION_DOWNSAMPLING",
                parameters={
                    "scale_factor": sf,
                    "original_gsd_m": source_gsd,
                    "effective_gsd_m": eff_gsd,
                    "resampling_method": "anti_aliased_area_averaging",
                    "DERIVED_FROM_REAL_DATA": True,
                },
                description=f"Anti-aliased downsampled OHRC raster to scale {sf:.2f}x (effective GSD {eff_gsd:.4f} m/px)",
            )

            derived_prod = LunarProduct(
                product_id=derived_meta.product_id,
                file_path=str(out_path),
                metadata=derived_meta,
                provenance=prov,
                validation=ValidationResult(is_valid=True),
                raster_data=img_to_save,
                is_synthetic=False,
            )

            p_level = PyramidLevel(
                level_index=idx,
                name=level_name,
                scale_factor=sf,
                effective_gsd_m=eff_gsd,
                lines=new_h,
                samples=new_w,
                resampling_method="anti_aliased_area_averaging",
                derived_image_path=out_path,
                derived_product=derived_prod,
            )
            pyramid_levels.append(p_level)

        return pyramid_levels

    def _downsample_memory_safe(
        self,
        raster: np.ndarray,
        target_size: Tuple[int, int],  # (width, height)
        scale_factor: float,
    ) -> np.ndarray:
        """Memory-safe anti-aliased downsampling using low-pass Gaussian blur pre-filtering followed by INTER_AREA."""
        target_w, target_h = target_size
        h, w = raster.shape[:2]

        # Apply low-pass Gaussian pre-filtering to prevent aliasing when downsampling > 1.5x
        if scale_factor > 1.5:
            sigma = (scale_factor / 2.0) - 0.2
            ksize = int(2 * math.ceil(2 * sigma) + 1)
            ksize = max(3, ksize if ksize % 2 != 0 else ksize + 1)
            blurred = cv2.GaussianBlur(raster, (ksize, ksize), sigmaX=sigma, sigmaY=sigma)
        else:
            blurred = raster

        # cv2.INTER_AREA is optimal for area-averaging decimation
        downsampled = cv2.resize(blurred, (target_w, target_h), interpolation=cv2.INTER_AREA)
        return downsampled
