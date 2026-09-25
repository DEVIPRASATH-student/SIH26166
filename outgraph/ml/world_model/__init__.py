"""LunarSynapse World Model Package.
Physics-Aware, Self-Evolving Multi-Modal Lunar World Model.
"""

from .entity import (
    EntityState,
    AssociationType,
    AssociationStatus,
    EntityAssociation,
    LunarEntity,
    EntityResolver,
)
from .evidence import (
    EvidenceType,
    EvidenceStatus,
    EvidenceProvenance,
    Evidence,
    EntityEvidenceProfile,
)
from .graph import (
    NodeType,
    EdgeRelation,
    WorldGraph,
)
from .uncertainty import (
    UncertaintyType,
    PhysicalUncertainty,
    UncertaintyChain,
    UncertaintyPropagator,
)
from .knowledge_gap import (
    GapType,
    GapSeverity,
    GapStatus,
    KnowledgeGap,
    KnowledgeGapDetector,
)
from .next_best_observation import (
    InformationGainPotential,
    SensorFeasibility,
    NextBestObservation,
    NextBestObservationEngine,
)
from .world_model_engine import (
    WorldModelEngine,
)
from .observation_matrix import (
    OverlapStatus,
    ObservationRecord,
    OverlapEvaluation,
    ObservationCompatibilityMatrix,
)
from .cross_sensor_validator import (
    ValidationCaseResult,
    CrossSensorEntityValidator,
)
from .evidence_fusion import (
    FusedEvidenceExplanation,
    EvidenceFusionEngine,
)
from .temporal import (
    TemporalState,
    TemporalObservationEpoch,
    TemporalAnalysisResult,
    TemporalReasoningEngine,
)
from .gap_benchmark import (
    KnowledgeGapBenchmark,
)
from .active_loop import (
    ActiveWorldModelLoop,
)
from .explainability import (
    EntityExplanationCard,
    ExplainabilityEngine,
)

__all__ = [
    "EntityState",
    "AssociationType",
    "AssociationStatus",
    "EntityAssociation",
    "LunarEntity",
    "EntityResolver",
    "EvidenceType",
    "EvidenceStatus",
    "EvidenceProvenance",
    "Evidence",
    "EntityEvidenceProfile",
    "NodeType",
    "EdgeRelation",
    "WorldGraph",
    "UncertaintyType",
    "PhysicalUncertainty",
    "UncertaintyChain",
    "UncertaintyPropagator",
    "GapType",
    "GapSeverity",
    "GapStatus",
    "KnowledgeGap",
    "KnowledgeGapDetector",
    "InformationGainPotential",
    "SensorFeasibility",
    "NextBestObservation",
    "NextBestObservationEngine",
    "WorldModelEngine",
    "OverlapStatus",
    "ObservationRecord",
    "OverlapEvaluation",
    "ObservationCompatibilityMatrix",
    "ValidationCaseResult",
    "CrossSensorEntityValidator",
    "FusedEvidenceExplanation",
    "EvidenceFusionEngine",
    "TemporalState",
    "TemporalObservationEpoch",
    "TemporalAnalysisResult",
    "TemporalReasoningEngine",
    "KnowledgeGapBenchmark",
    "ActiveWorldModelLoop",
    "EntityExplanationCard",
    "ExplainabilityEngine",
]
