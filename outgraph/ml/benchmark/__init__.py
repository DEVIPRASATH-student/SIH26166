"""LunarSynapse ML Benchmark & Correspondence Baseline Package."""

from .pair_registry import BenchmarkPair, RealDataPairRegistry
from .ground_truth import GroundTruthLevel, evaluate_ground_truth_level
from .metrics import BenchmarkMetrics, MatcherImplementationStatus
from .failure_classifier import CorrespondenceOutcome, FailureCategory, classify_correspondence_failure

__all__ = [
    "BenchmarkPair",
    "RealDataPairRegistry",
    "GroundTruthLevel",
    "evaluate_ground_truth_level",
    "BenchmarkMetrics",
    "MatcherImplementationStatus",
    "CorrespondenceOutcome",
    "FailureCategory",
    "classify_correspondence_failure",
]
