"""Content-Type enforcement for state-changing requests.

Any POST/PUT/PATCH request with a body must declare `application/json`.
Prevents content-type confusion / MIME-sniffing attacks and blocks naive
cross-origin form submissions that bypass CORS preflight.
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_MUTATING = {"POST", "PUT", "PATCH"}
_ALLOWED_PREFIXES = ("application/json",)

# Paths that legitimately accept other content types (e.g. file uploads, SSE).
_EXEMPT_PATH_PREFIXES: tuple[str, ...] = (
    # Add any multipart upload paths here when introduced.
)


class ContentTypeGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in _MUTATING:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(p) for p in _EXEMPT_PATH_PREFIXES):
            return await call_next(request)

        cl = request.headers.get("content-length", "0")
        if cl.isdigit() and int(cl) == 0:
            return await call_next(request)

        ct = (request.headers.get("content-type") or "").lower()
        if not any(ct.startswith(p) for p in _ALLOWED_PREFIXES):
            return JSONResponse(
                status_code=415,
                content={
                    "ok": False,
                    "error": {
                        "code": "unsupported_media_type",
                        "message": "Content-Type must be application/json.",
                    },
                },
            )
        return await call_next(request)
