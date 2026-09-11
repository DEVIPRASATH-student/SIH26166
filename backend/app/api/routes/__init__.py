"""API Routes Package."""

from .observations import router as observations_router
from .correspondence import router as correspondence_router
from .registration import router as registration_router
from .entities import router as entities_router
from .graph import router as graph_router
from .uncertainty import router as uncertainty_router
from .knowledge import router as knowledge_router
from .recommendation import router as recommendation_router
from .benchmark import router as benchmark_router
from .red_team import router as red_team_router
from .demo import router as demo_router
from .system import router as system_router

__all__ = [
    "observations_router",
    "correspondence_router",
    "registration_router",
    "entities_router",
    "graph_router",
    "uncertainty_router",
    "knowledge_router",
    "recommendation_router",
    "benchmark_router",
    "red_team_router",
    "demo_router",
    "system_router",
]
