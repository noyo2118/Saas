"""Liveness / readiness endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.cache.redis import cache
from app.core.config import settings
from app.intelligence.registry import all_providers_meta

router = APIRouter(tags=["health"])


@router.get("/health", include_in_schema=True)
async def health() -> dict:
    return {"ok": True, "status": "healthy", "version": settings.APP_VERSION}


@router.get("/health/live", include_in_schema=False)
async def live() -> dict:
    return {"ok": True}


@router.get("/health/ready", include_in_schema=False)
async def ready() -> dict:
    cache_ok = await cache.ping()
    return {
        "ok": cache_ok,
        "cache": "ok" if cache_ok else "degraded",
        "cache_backend": cache.backend_name,
        "providers": all_providers_meta(),
    }
