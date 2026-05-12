"""Body size limit middleware — guard against DoS via oversized uploads."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds ``MAX_REQUEST_BYTES``.

    Does not buffer the entire request body — it reads the Content-Length
    header and rejects early. Streaming clients that omit Content-Length
    are still bounded by Starlette's own read loop.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        limit = settings.MAX_REQUEST_BYTES
        if limit > 0:
            cl = request.headers.get("content-length")
            if cl and cl.isdigit() and int(cl) > limit:
                return JSONResponse(
                    status_code=413,
                    content={
                        "ok": False,
                        "error": {
                            "code": "payload_too_large",
                            "message": f"Request body exceeds {limit} bytes.",
                        },
                    },
                )
        return await call_next(request)
