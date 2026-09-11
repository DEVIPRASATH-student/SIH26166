"""LunarSynapse FastAPI Backend Application.
Physics-Aware, Self-Evolving Multi-Modal Lunar World Model.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .core.logging import logger
from .database.session import init_db
from .api.routes import (
    observations_router,
    correspondence_router,
    registration_router,
    entities_router,
    graph_router,
    uncertainty_router,
    knowledge_router,
    recommendation_router,
    benchmark_router,
    red_team_router,
    demo_router,
    system_router,
)

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} Backend...")
    init_db()
    logger.info("Database schemas initialized.")


# Register API Routers
app.include_router(observations_router, prefix=settings.API_PREFIX)
app.include_router(correspondence_router, prefix=settings.API_PREFIX)
app.include_router(registration_router, prefix=settings.API_PREFIX)
app.include_router(entities_router, prefix=settings.API_PREFIX)
app.include_router(graph_router, prefix=settings.API_PREFIX)
app.include_router(uncertainty_router, prefix=settings.API_PREFIX)
app.include_router(knowledge_router, prefix=settings.API_PREFIX)
app.include_router(recommendation_router, prefix=settings.API_PREFIX)
app.include_router(benchmark_router, prefix=settings.API_PREFIX)
app.include_router(red_team_router, prefix=settings.API_PREFIX)
app.include_router(demo_router, prefix=settings.API_PREFIX)
app.include_router(system_router, prefix=settings.API_PREFIX)


@app.get("/")
def root_endpoint():
    return {
        "project": settings.PROJECT_NAME,
        "title": "Physics-Aware, Self-Evolving Multi-Modal Lunar World Model",
        "tagline": "Others register images. LunarSynapse builds a memory and reasoning layer for the Moon.",
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_PREFIX}/system/health",
        "disclaimer": "DEMO / SYNTHETIC DATA - Physics-grounded lunar intelligence simulation",
    }
