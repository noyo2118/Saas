"""Trusted-host middleware — prevents Host header injection.

In production, the Host header value is validated against ``TRUSTED_HOSTS``.
Requests with an unexpected Host are rejected with 400. In development this
check is skipped to keep local tooling (localhost, 127.0.0.1, LAN IPs) happy.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


def _matches(host: str, patterns: list[str]) -> bool:
    host = (host or "").split(":")[0].lower()
    for p in patterns:
        p = p.lower()
        if p == "*" or p == host:
            return True
        if p.startswith("*.") and host.endswith(p[1:]):
            return True
    return False


class TrustedHostMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.is_production:
            return await call_next(request)
        if not settings.TRUSTED_HOSTS:
            return await call_next(request)
        host = request.headers.get("host", "")
        if not _matches(host, settings.TRUSTED_HOSTS):
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": {"code": "bad_host", "message": "Invalid host header."},
                },
            )
        return await call_next(request)
