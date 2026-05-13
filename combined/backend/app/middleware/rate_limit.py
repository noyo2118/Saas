"""Per-IP / per-path rate limiting backed by the cache layer.

Three tiers:
    - scan routes:  RATE_LIMIT_SCAN_PER_MIN
    - auth routes:  RATE_LIMIT_AUTH_PER_MIN
    - everything:   RATE_LIMIT_GLOBAL_PER_MIN

The limiter is best-effort and fails-open if the cache backend is unavailable.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.core.exceptions import RateLimitError

_EXEMPT_PATHS = {"/health", "/health/ready", "/health/live", "/", "/docs", "/redoc", "/openapi.json"}


def _classify(path: str) -> tuple[str, int]:
    if path.startswith(f"{settings.API_V1_PREFIX}/auth"):
        return "auth", settings.RATE_LIMIT_AUTH_PER_MIN
    if (
        path.startswith(f"{settings.API_V1_PREFIX}/scans")
        or path.startswith(f"{settings.API_V1_PREFIX}/url")
        or path.startswith(f"{settings.API_V1_PREFIX}/ip")
        or path.startswith(f"{settings.API_V1_PREFIX}/domain")
    ):
        return "scan", settings.RATE_LIMIT_SCAN_PER_MIN
    return "global", settings.RATE_LIMIT_GLOBAL_PER_MIN


def _client_identity(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in _EXEMPT_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        bucket, limit = _classify(path)
        identity = _client_identity(request)
        key = ns.rate_limit(bucket, identity)

        try:
            count = await cache.incr(key, ttl=60)
        except Exception:  # noqa: BLE001 - fail open
            return await call_next(request)

        if count > limit:
            raise RateLimitError(
                message=f"Rate limit exceeded for {bucket} ({limit}/min).",
                details={"bucket": bucket, "limit": limit, "identity": identity},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
