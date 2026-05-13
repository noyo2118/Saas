"""TrustScan — AI Cyber Threat Intelligence Platform.

FastAPI application factory. Defensive middleware stack order (outermost first):

    RequestIdMiddleware           → trace id + access log
    SecurityHeadersMiddleware     → OWASP response headers
    TrustedHostMiddleware         → Host header validation (prod)
    BodySizeLimitMiddleware       → 413 on oversized payloads
    ContentTypeGuardMiddleware    → reject non-JSON mutations
    GZipMiddleware                → compress large responses
    CORSMiddleware                → CORS allowlist
    IPGateMiddleware              → deny banned IPs before anything expensive
    RateLimitMiddleware           → per-IP / per-bucket counter

Run:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop uvloop --http httptools
"""
from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse, PlainTextResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.lifespan import lifespan
from app.middleware.body_limit import BodySizeLimitMiddleware
from app.middleware.content_type import ContentTypeGuardMiddleware
from app.middleware.ip_gate import IPGateMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.middleware.trusted_host import TrustedHostMiddleware
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

    # ------------------------------------------------------------------ middleware
    # Starlette executes add_middleware in reverse order, so the *last* one added
    # runs first. We add them in outermost-first order; the effective execution
    # order matches the module docstring above.
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(IPGateMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["authorization", "content-type", "x-request-id"],
        expose_headers=["X-Request-ID", "X-Trace-ID"],
        max_age=600,
    )
    app.add_middleware(GZipMiddleware, minimum_size=512)
    app.add_middleware(ContentTypeGuardMiddleware)
    app.add_middleware(BodySizeLimitMiddleware)
    app.add_middleware(TrustedHostMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestIdMiddleware)

    # ------------------------------------------------------------------ exceptions
    register_exception_handlers(app)

    # ------------------------------------------------------------------ routers
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # ------------------------------------------------------------------ well-known
    @app.get("/.well-known/security.txt", include_in_schema=False)
    async def security_txt() -> PlainTextResponse:
        body = (
            "Contact: mailto:security@trustscan.ai\n"
            "Expires: 2030-01-01T00:00:00Z\n"
            "Preferred-Languages: en\n"
            "Policy: https://github.com/noyo2118/Saas/blob/main/SECURITY.md\n"
        )
        return PlainTextResponse(body, media_type="text/plain")

    @app.get("/robots.txt", include_in_schema=False)
    async def robots_txt() -> PlainTextResponse:
        return PlainTextResponse("User-agent: *\nDisallow:\n", media_type="text/plain")

    @app.get("/", tags=["health"], include_in_schema=False)
    async def root() -> dict:
        return {
            "ok": True,
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "env": settings.APP_ENV,
            "docs": "/docs" if not settings.is_production else None,
            "api": settings.API_V1_PREFIX,
        }

    log.info("app_created", extra={
        "app": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.APP_ENV,
    })
    return app


app = create_app()
