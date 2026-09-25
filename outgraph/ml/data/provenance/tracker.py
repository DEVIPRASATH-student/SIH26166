"""Provenance and Traceability Engine.
Calculates SHA256 file checksums, records ingestion history, and tracks all data transformations.
"""

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..models import ProvenanceRecord


class ProvenanceTracker:
    """Computes file hashes and logs data provenance."""

    @staticmethod
    def calculate_sha256(file_path: Path, block_size: int = 65536) -> Optional[str]:
        """Calculates SHA256 checksum for a file."""
        if not file_path.exists() or not file_path.is_file():
            return None
        hasher = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(block_size), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    @classmethod
    def create_record(
        cls,
        source_name: str,
        file_path: Path,
        product_id: str,
        metadata_extraction_status: str = "COMPLETED",
    ) -> ProvenanceRecord:
        """Creates an initial provenance record for an ingested file."""
        checksum = cls.calculate_sha256(file_path)
        return ProvenanceRecord(
            source_name=source_name,
            original_filename=file_path.name,
            product_id=product_id,
            ingestion_timestamp=datetime.utcnow(),
            sha256_checksum=checksum,
            metadata_extraction_status=metadata_extraction_status,
            processing_history=[
                {
                    "step": "INGESTION",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": f"File ingested from {source_name}",
                }
            ],
        )

    @staticmethod
    def record_transformation(
        record: ProvenanceRecord,
        operation_name: str,
        parameters: Dict[str, Any],
        description: str,
    ) -> ProvenanceRecord:
        """Appends a transformation step to the provenance record."""
        step_entry = {
            "step": operation_name,
            "timestamp": datetime.utcnow().isoformat(),
            "parameters": parameters,
            "description": description,
        }
        record.processing_history.append(step_entry)
        return record
