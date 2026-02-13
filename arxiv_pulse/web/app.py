"""
FastAPI Application Entry Point
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine

from arxiv_pulse.models import Base, Database
from arxiv_pulse.web.api import collections, config, export, papers, stats, tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/arxiv_papers.db")
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    db = Database(db_url)
    db.init_default_config()
    yield


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="arXiv Pulse",
        description="Intelligent arXiv literature crawler and analyzer",
        version="0.9.0",
        lifespan=lifespan,
    )

    api_router = FastAPI(prefix="/api")
    api_router.include_router(papers.router, prefix="/papers", tags=["papers"])
    api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
    api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
    api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
    api_router.include_router(export.router, prefix="/export", tags=["export"])
    api_router.include_router(config.router, prefix="/config", tags=["config"])

    app.mount("/api", api_router)

    static_path = Path(__file__).parent / "static"
    if static_path.exists() and any(static_path.iterdir()):
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "0.9.0"}

    return app


app = create_app()
