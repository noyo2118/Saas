"""IP gate middleware — refuse requests from banned IPs.

Checked before rate limiting. When an IP is banned the response is a generic
403 with no reveal of the ban reason (to avoid tipping off attackers).
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.exceptions import ForbiddenError
from app.security.ipban import is_banned


def _client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class IPGateMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)
        ip = _client_ip(request)
        try:
            if await is_banned(ip):
                raise ForbiddenError("Access denied.")
        except ForbiddenError:
            raise
        except Exception:  # noqa: BLE001 - fail open if cache is unreachable
            pass
        return await call_next(request)
