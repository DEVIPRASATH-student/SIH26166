"""Product Ingestion Orchestration Engine.
Selects the appropriate adapter, executes metadata extraction, data loading,
validation, and provenance hashing for real scientific lunar products.
"""

from pathlib import Path
from typing import List, Optional, Union

from .base import BaseIngestionAdapter
from .issdc_adapter import ISSDCAdapter
from .lroc_adapter import LROCAdapter
from .selene_adapter import SELENEAdapter
from .generic_adapter import GenericAdapter
from ..models import LunarProduct


class ProductIngestionEngine:
    """Master ingestion factory and orchestrator."""

    def __init__(self, adapters: Optional[List[BaseIngestionAdapter]] = None):
        self.adapters = adapters or [
            ISSDCAdapter(),
            LROCAdapter(),
            SELENEAdapter(),
            GenericAdapter(),
        ]

    def select_adapter(self, file_path: Path, source_override: Optional[str] = None) -> BaseIngestionAdapter:
        """Selects adapter based on explicit source override or auto-detection."""
        if source_override:
            src_upper = source_override.upper()
            if "ISSDC" in src_upper or "CHANDRAYAAN" in src_upper:
                return ISSDCAdapter()
            if "LROC" in src_upper or "LRO" in src_upper:
                return LROCAdapter()
            if "SELENE" in src_upper or "KAGUYA" in src_upper:
                return SELENEAdapter()

        for adapter in self.adapters:
            if adapter.can_ingest(file_path):
                return adapter

        return GenericAdapter()

    def ingest_product(self, file_path: Union[str, Path], source: Optional[str] = None) -> LunarProduct:
        """Main entry point for ingesting a local lunar product file."""
        path = Path(file_path)
        adapter = self.select_adapter(path, source_override=source)
        return adapter.ingest_product(path)
