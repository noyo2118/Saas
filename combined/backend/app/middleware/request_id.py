"""Request-id / trace-id middleware.

Attaches a short UUID trace_id to every request and exposes it via
``request.state.trace_id``, the ``X-Request-ID`` response header, and
every log line emitted during that request's lifetime.
"""
from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.telemetry.logger import get_logger

log = get_logger("http.access")


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Inject a trace id, measure latency, emit a single structured access log."""

    HEADER = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        incoming = request.headers.get(self.HEADER)
        trace_id = incoming or uuid.uuid4().hex[:16]
        request.state.trace_id = trace_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)
            log.exception(
                "request_failed",
                extra={
                    "trace_id": trace_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                },
            )
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers[self.HEADER] = trace_id
        response.headers["X-Trace-ID"] = trace_id
        log.info(
            "request",
            extra={
                "trace_id": trace_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
                "ip": request.client.host if request.client else None,
            },
        )
        return response
