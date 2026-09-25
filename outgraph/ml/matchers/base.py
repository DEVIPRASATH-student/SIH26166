"""Base Matcher Interface and Data Structures."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


@dataclass
class KeypointFeature:
    x: float
    y: float
    size: float = 1.0
    angle: float = 0.0
    response: float = 1.0
    octave: int = 0


@dataclass
class MatchResult:
    source_points: np.ndarray  # [N, 2] float32 (x, y)
    target_points: np.ndarray  # [N, 2] float32 (x, y)
    match_distances: np.ndarray  # [N] float32
    raw_confidence: float  # [0, 1] average match confidence
    algorithm_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def num_matches(self) -> int:
        return len(self.source_points)


class BaseMatcher(ABC):
    """Abstract interface for all feature extractors and cross-modal matchers."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def extract_features(
        self, image: np.ndarray
    ) -> Tuple[List[KeypointFeature], np.ndarray]:
        """Extracts keypoints and feature descriptors from an input grayscale/RGB image.
        Returns:
            keypoints: List of KeypointFeature
            descriptors: np.ndarray of shape [N, D]
        """
        pass

    @abstractmethod
    def match(
        self,
        source_image: np.ndarray,
        target_image: np.ndarray,
        ratio_threshold: float = 0.80,
    ) -> MatchResult:
        """Finds candidate 2D-to-2D correspondences between source and target images."""
        pass

    def get_confidence(self, match_result: MatchResult) -> float:
        """Calculates raw visual confidence for the match set."""
        if match_result.num_matches == 0:
            return 0.0
        # Inverse distance or score
        return float(match_result.raw_confidence)
