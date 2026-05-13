"""Application startup and shutdown hooks."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.cache.redis import cache as cache_backend
from app.database.session import dispose_engine, init_db
from app.services.http_client import close_client
from app.telemetry.logger import get_logger

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup_begin")

    await cache_backend.connect()
    log.info("cache_connected", extra={"backend": cache_backend.backend_name})

    await init_db()
    log.info("database_ready")

    from app.websocket.manager import manager as ws_manager
    app.state.ws_manager = ws_manager

    log.info("startup_complete")
    yield
    log.info("shutdown_begin")

    await close_client()
    await cache_backend.disconnect()
    await dispose_engine()
    log.info("shutdown_complete")
