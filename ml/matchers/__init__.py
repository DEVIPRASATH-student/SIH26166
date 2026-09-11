"""Feature Matchers Package.
Contains classical baselines (SIFT, ORB) and deep learning adapters (SuperPoint, LoFTR, RIFT).
"""
from .base import BaseMatcher, MatchResult, KeypointFeature
from .sift_matcher import SIFTMatcher
from .orb_matcher import ORBMatcher
from .adapters import SuperPointAdapter, LoFTRAdapter, RIFTAdapter, get_matcher

__all__ = [
    "BaseMatcher",
    "MatchResult",
    "KeypointFeature",
    "SIFTMatcher",
    "ORBMatcher",
    "SuperPointAdapter",
    "LoFTRAdapter",
    "RIFTAdapter",
    "get_matcher",
]
