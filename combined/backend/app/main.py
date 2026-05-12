"""TrustScan — AI Cyber Threat Intelligence Platform.

FastAPI application factory. All runtime wiring happens here: logging,
middleware stack, exception handlers, OpenAPI metadata, API v1 routers,
lifespan hooks, and the async ORJSON response class.

Run:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop uvloop --http httptools
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.monitoring.health import router as health_router
from app.telemetry.logger import configure_logging, get_logger

# uvloop for Linux
try:
    import uvloop  # type: ignore
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except Exception:  # noqa: BLE001
    pass

configure_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON)
log = get_logger(__name__)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Enterprise-grade AI cyber threat intelligence platform. "
            "Real-time scanning of URLs, domains, IPs and email domains "
            "with AI-generated intelligence reports."
        ),
        default_response_class=ORJSONResponse,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        openapi_tags=[
            {"name": "auth", "description": "Email-OTP authentication."},
            {"name": "scans", "description": "Target scan orchestration."},
            {"name": "intelligence", "description": "Raw intelligence lookups."},
            {"name": "url", "description": "URL / website analysis."},
            {"name": "ip", "description": "IP intelligence."},
            {"name": "domain", "description": "Domain / WHOIS / DNS."},
            {"name": "reputation", "description": "Reputation & blacklist feeds."},
            {"name": "users", "description": "Account profile."},
            {"name": "admin", "description": "Administrative endpoints."},
            {"name": "ws", "description": "Websocket channels."},
            {"name": "health", "description": "Liveness & readiness."},
        ],
    )

    # middleware (order matters)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(GZipMiddleware, minimum_size=512)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Trace-ID"],
    )
    app.add_middleware(RateLimitMiddleware)

    register_exception_handlers(app)

    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", tags=["health"], include_in_schema=False)
    async def root() -> dict:
        return {
            "ok": True,
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "docs": "/docs",
            "api": settings.API_V1_PREFIX,
        }

    log.info("app_created", extra={
        "app": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.APP_ENV,
    })
    return app


app = create_app()
