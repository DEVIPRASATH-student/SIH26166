"""Abstract Base Ingestion Adapter Interface.
Defines standard contract for sensor-specific product loaders.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Tuple, Any
import numpy as np

from ..models import ProductMetadata, LunarProduct, ProvenanceRecord, ValidationResult
from ..validation.validator import ProductValidator
from ..provenance.tracker import ProvenanceTracker


class BaseIngestionAdapter(ABC):
    """Abstract Base Class for product-specific ingestion adapters."""

    def __init__(self, source_name: str):
        self.source_name = source_name

    @abstractmethod
    def can_ingest(self, file_path: Path) -> bool:
        """Determines if this adapter can ingest the given product file."""
        pass

    @abstractmethod
    def extract_metadata(self, file_path: Path) -> ProductMetadata:
        """Extracts available metadata directly from product label/headers.
        MUST NOT fabricate missing values or overwrite actual GSD with nominal specs.
        """
        pass

    @abstractmethod
    def load_raster_data(self, file_path: Path, metadata: ProductMetadata) -> Tuple[Optional[np.ndarray], List[str]]:
        """Loads raster data as numpy array preserving native precision/bands."""
        pass

    def ingest_product(self, file_path: Path) -> LunarProduct:
        """Standard ingestion pipeline: extract metadata -> load raster -> validate -> hash provenance."""
        product_id = file_path.stem
        metadata = self.extract_metadata(file_path)
        raster_data, load_warnings = self.load_raster_data(file_path, metadata)

        validation = ProductValidator.validate_product(file_path, metadata, raster_data)
        validation.warnings.extend(load_warnings)

        provenance = ProvenanceTracker.create_record(
            source_name=self.source_name,
            file_path=file_path,
            product_id=metadata.product_id or product_id,
            metadata_extraction_status="SUCCESS" if validation.is_valid else "VALIDATION_WARNINGS",
        )

        return LunarProduct(
            product_id=metadata.product_id or product_id,
            file_path=str(file_path.resolve()),
            metadata=metadata,
            provenance=provenance,
            validation=validation,
            raster_data=raster_data,
            is_synthetic=False,  # Real product path
        )
