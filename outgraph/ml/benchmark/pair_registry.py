"""Real Lunar Data Pair Registry and Discovery Engine.

Supports pair hierarchy:
  Priority 1: OHRC ↔ LRO NAC (High-res optical baseline)
  Priority 2: OHRC ↔ TMC-2 (Chandrayaan-2 cross-instrument scale difference)
  Priority 3: TMC-2 ↔ LRO NAC (Cross-resolution coverage difference)
  Priority 4: IIRS ↔ Optical imagery (Multimodal spectral case)
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import logging

from .ground_truth import GroundTruthLevel

logger = logging.getLogger("LunarSynapse.ML.PairRegistry")


@dataclass
class BenchmarkPair:
    pair_id: str
    source_sensor: str
    target_sensor: str
    source_product_id: str
    target_product_id: str
    source_file_path: str
    target_file_path: str
    priority_tier: int  # 1 to 4
    expected_difficulty: str  # "low", "medium", "high", "very_high"
    is_real_data: bool = True
    ground_truth_level: GroundTruthLevel = GroundTruthLevel.UNKNOWN
    acquisition_info_status: str = "UNKNOWN"
    spatial_metadata_status: str = "UNKNOWN"
    gsd_status: str = "UNKNOWN"
    overlap_status: str = "UNKNOWN"
    notes: str = ""
    provenance: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pair_id": self.pair_id,
            "source_sensor": self.source_sensor,
            "target_sensor": self.target_sensor,
            "source_product_id": self.source_product_id,
            "target_product_id": self.target_product_id,
            "source_file_path": self.source_file_path,
            "target_file_path": self.target_file_path,
            "priority_tier": self.priority_tier,
            "expected_difficulty": self.expected_difficulty,
            "is_real_data": self.is_real_data,
            "ground_truth_level": self.ground_truth_level.to_string(),
            "acquisition_info_status": self.acquisition_info_status,
            "spatial_metadata_status": self.spatial_metadata_status,
            "gsd_status": self.gsd_status,
            "overlap_status": self.overlap_status,
            "notes": self.notes,
            "provenance": self.provenance,
        }


class RealDataPairRegistry:
    """Registry managing discovered real-data pairs and synthetic controls."""

    def __init__(self, data_root: str = "data/real"):
        self.data_root = self._resolve_data_root(data_root)
        self.pairs: Dict[str, BenchmarkPair] = {}
        self._initialize_registry()

    @staticmethod
    def _resolve_data_root(data_root: str) -> str:
        """Resolves data_root robustly across repository execution contexts."""
        if not data_root:
            return data_root
        p = Path(data_root)
        if p.is_absolute():
            return str(p)
        if p.exists():
            return str(p)
        try:
            curr_file = Path(__file__).resolve()
            for parent in curr_file.parents:
                candidate = parent / p
                if candidate.exists():
                    return str(candidate.resolve())
        except Exception:
            pass
        return str(p)

    def _initialize_registry(self):
        """Scans local data/real directory or loads pair definitions."""
        # 1. Discover local files in data/real if any exist
        if os.path.exists(self.data_root):
            self._scan_data_directory()

        # 2. Check for explicit pair manifest at data/real/pairs.json
        manifest_path = os.path.join(self.data_root, "pairs.json")
        if os.path.exists(manifest_path):
            self.load_from_manifest(manifest_path)

    def _scan_data_directory(self):
        """Scans folder structure for matching pairs."""
        ohrc_dir = os.path.join(self.data_root, "chandrayaan2", "ohrc")
        if not os.path.exists(ohrc_dir):
            ohrc_dir = os.path.join(self.data_root, "ohrc")
        tmc2_dir = os.path.join(self.data_root, "chandrayaan2", "tmc2")
        if not os.path.exists(tmc2_dir):
            tmc2_dir = os.path.join(self.data_root, "tmc2")
        iirs_dir = os.path.join(self.data_root, "chandrayaan2", "iirs")
        if not os.path.exists(iirs_dir):
            iirs_dir = os.path.join(self.data_root, "iirs")
        nac_dir = os.path.join(self.data_root, "lro", "nac")
        if not os.path.exists(nac_dir):
            nac_dir = os.path.join(self.data_root, "lro_nac")
        selene_dir = os.path.join(self.data_root, "selene", "terrain")
        if not os.path.exists(selene_dir):
            selene_dir = os.path.join(self.data_root, "selene")

        # Auto-pair files if matching pairs are found in directories
        ohrc_files = self._get_valid_files(ohrc_dir)
        nac_files = self._get_valid_files(nac_dir)
        tmc2_files = self._get_valid_files(tmc2_dir)
        iirs_files = self._get_valid_files(iirs_dir)

        # Pair Priority 1: OHRC ↔ LRO NAC
        for i, o_file in enumerate(ohrc_files):
            for j, n_file in enumerate(nac_files):
                pair_id = f"REAL_OHRC_LRO_{i+1:03d}_{j+1:03d}"
                self.pairs[pair_id] = BenchmarkPair(
                    pair_id=pair_id,
                    source_sensor="OHRC",
                    target_sensor="LRO_NAC",
                    source_product_id=os.path.basename(o_file),
                    target_product_id=os.path.basename(n_file),
                    source_file_path=o_file,
                    target_file_path=n_file,
                    priority_tier=1,
                    expected_difficulty="medium",
                    is_real_data=True,
                    notes="High-resolution optical cross-mission pair",
                )

        # Pair Priority 2: OHRC ↔ TMC-2
        for i, o_file in enumerate(ohrc_files):
            for j, t_file in enumerate(tmc2_files):
                pair_id = f"REAL_OHRC_TMC2_{i+1:03d}_{j+1:03d}"
                self.pairs[pair_id] = BenchmarkPair(
                    pair_id=pair_id,
                    source_sensor="OHRC",
                    target_sensor="TMC-2",
                    source_product_id=os.path.basename(o_file),
                    target_product_id=os.path.basename(t_file),
                    source_file_path=o_file,
                    target_file_path=t_file,
                    priority_tier=2,
                    expected_difficulty="high",
                    is_real_data=True,
                    overlap_status="OVERLAPPING",
                    notes="Chandrayaan-2 high vs medium resolution scale gap pair (OHRC 0.26m, TMC-2 6.07m)",
                )

        # Pair Priority 3: TMC-2 ↔ LRO NAC
        for i, t_file in enumerate(tmc2_files):
            for j, n_file in enumerate(nac_files):
                pair_id = f"REAL_TMC2_LRO_{i+1:03d}_{j+1:03d}"
                self.pairs[pair_id] = BenchmarkPair(
                    pair_id=pair_id,
                    source_sensor="TMC-2",
                    target_sensor="LRO_NAC",
                    source_product_id=os.path.basename(t_file),
                    target_product_id=os.path.basename(n_file),
                    source_file_path=t_file,
                    target_file_path=n_file,
                    priority_tier=3,
                    expected_difficulty="high",
                    is_real_data=True,
                    notes="TMC-2 to LRO NAC cross-resolution pair",
                )

        # Pair Priority 4: IIRS ↔ Optical (OHRC or TMC-2)
        for i, ii_file in enumerate(iirs_files):
            for j, o_file in enumerate(ohrc_files + tmc2_files):
                pair_id = f"REAL_IIRS_OPTICAL_{i+1:03d}_{j+1:03d}"
                tgt_sensor = "OHRC" if "ohrc" in o_file.lower() else "TMC-2"
                self.pairs[pair_id] = BenchmarkPair(
                    pair_id=pair_id,
                    source_sensor="IIRS",
                    target_sensor=tgt_sensor,
                    source_product_id=os.path.basename(ii_file),
                    target_product_id=os.path.basename(o_file),
                    source_file_path=ii_file,
                    target_file_path=o_file,
                    priority_tier=4,
                    expected_difficulty="very_high",
                    is_real_data=True,
                    notes="IIRS single-band vs optical multimodal baseline pair",
                )

    def _get_valid_files(self, directory: str) -> List[str]:
        if not os.path.exists(directory):
            return []
        valid_exts = {".xml", ".xml.lbl", ".lbl", ".tif", ".tiff", ".png", ".jpg"}
        primary_files = []
        for root, _, filenames in os.walk(directory):
            xml_files = [f for f in filenames if f.lower().endswith(".xml") and not f.startswith(".")]
            data_xmls = [
                f for f in xml_files
                if ("_d_img_" in f.lower() or ("data" in root.lower() and "calibrated" in root.lower()))
                and not f.endswith("_b_brw_d18.xml") and not f.endswith("_g_grd_d18.xml")
            ]
            if data_xmls:
                for fn in data_xmls:
                    primary_files.append(os.path.join(root, fn))
            elif xml_files:
                for fn in xml_files:
                    if not fn.endswith("_b_brw_d18.xml") and not fn.endswith("_g_grd_d18.xml"):
                        primary_files.append(os.path.join(root, fn))
            else:
                for fn in filenames:
                    ext = os.path.splitext(fn)[1].lower()
                    if ext in valid_exts and not fn.startswith(".") and not fn.startswith("diff_") and not fn.startswith("reg_") and not fn.startswith("synth_"):
                        if "_b_brw_" not in fn.lower() and "_g_grd_" not in fn.lower():
                            primary_files.append(os.path.join(root, fn))
        return sorted(list(set(primary_files)))

    def load_from_manifest(self, manifest_path: str):
        """Loads structured pair metadata manifest from JSON."""
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data.get("pairs", []):
                pair = BenchmarkPair(
                    pair_id=item["pair_id"],
                    source_sensor=item["source_sensor"],
                    target_sensor=item["target_sensor"],
                    source_product_id=item["source_product_id"],
                    target_product_id=item["target_product_id"],
                    source_file_path=item["source_file_path"],
                    target_file_path=item["target_file_path"],
                    priority_tier=item.get("priority_tier", 1),
                    expected_difficulty=item.get("expected_difficulty", "medium"),
                    is_real_data=item.get("is_real_data", True),
                    ground_truth_level=GroundTruthLevel(item.get("ground_truth_level", 0)),
                    acquisition_info_status=item.get("acquisition_info_status", "UNKNOWN"),
                    spatial_metadata_status=item.get("spatial_metadata_status", "UNKNOWN"),
                    gsd_status=item.get("gsd_status", "UNKNOWN"),
                    overlap_status=item.get("overlap_status", "UNKNOWN"),
                    notes=item.get("notes", ""),
                    provenance=item.get("provenance", {}),
                )
                self.pairs[pair.pair_id] = pair
        except Exception as e:
            logger.error(f"Failed to load pair manifest from {manifest_path}: {e}")

    def register_pair(self, pair: BenchmarkPair):
        """Programmatically registers a benchmark pair."""
        self.pairs[pair.pair_id] = pair

    def get_pair(self, pair_id: str) -> Optional[BenchmarkPair]:
        return self.pairs.get(pair_id)

    def list_pairs(self, priority_tier: Optional[int] = None, real_only: bool = False) -> List[BenchmarkPair]:
        res = list(self.pairs.values())
        if priority_tier is not None:
            res = [p for p in res if p.priority_tier == priority_tier]
        if real_only:
            res = [p for p in res if p.is_real_data]
        return sorted(res, key=lambda p: (p.priority_tier, p.pair_id))
