"""Typed application exceptions and centralised exception handlers."""
from __future__ import annotations

from typing import Any, Optional

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.telemetry.logger import get_logger

log = get_logger(__name__)


class TrustScanError(Exception):
    code: str = "internal_error"
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Internal server error."

    def __init__(
        self,
        message: Optional[str] = None,
        *,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        if message:
            self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(TrustScanError):
    code = "validation_error"
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    message = "Request payload is invalid."


class NotFoundError(TrustScanError):
    code = "not_found"
    status_code = status.HTTP_404_NOT_FOUND
    message = "Resource not found."


class UnauthorizedError(TrustScanError):
    code = "unauthorized"
    status_code = status.HTTP_401_UNAUTHORIZED
    message = "Authentication required."


class ForbiddenError(TrustScanError):
    code = "forbidden"
    status_code = status.HTTP_403_FORBIDDEN
    message = "You do not have permission to perform this action."


class ConflictError(TrustScanError):
    code = "conflict"
    status_code = status.HTTP_409_CONFLICT
    message = "Resource conflict."


class RateLimitError(TrustScanError):
    code = "rate_limited"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = "Too many requests."


class SSRFBlockedError(TrustScanError):
    code = "ssrf_blocked"
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Target address is not allowed."


class InvalidTargetError(TrustScanError):
    code = "invalid_target"
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Invalid scan target."


class ScanFailedError(TrustScanError):
    code = "scan_failed"
    status_code = status.HTTP_502_BAD_GATEWAY
    message = "Scan could not be completed."


class UpstreamError(TrustScanError):
    code = "upstream_error"
    status_code = status.HTTP_502_BAD_GATEWAY
    message = "Upstream intelligence provider error."


class OTPInvalidError(TrustScanError):
    code = "otp_invalid"
    status_code = status.HTTP_400_BAD_REQUEST
    message = "Invalid or expired OTP."


class OTPCooldownError(TrustScanError):
    code = "otp_cooldown"
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    message = "Please wait before requesting another OTP."


def _envelope(
    *, code: str, message: str, status_code: int,
    trace_id: Optional[str], details: Optional[dict[str, Any]] = None,
) -> ORJSONResponse:
    body: dict[str, Any] = {
        "ok": False,
        "error": {"code": code, "message": message, "trace_id": trace_id},
    }
    if details:
        body["error"]["details"] = details
    return ORJSONResponse(status_code=status_code, content=body)


async def trustscan_exception_handler(request: Request, exc: TrustScanError):
    trace_id = getattr(request.state, "trace_id", None)
    log.warning("domain_error", extra={"code": exc.code, "path": request.url.path, "trace_id": trace_id})
    return _envelope(code=exc.code, message=exc.message, status_code=exc.status_code,
                     trace_id=trace_id, details=exc.details or None)


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    trace_id = getattr(request.state, "trace_id", None)
    return _envelope(
        code="http_error",
        message=str(exc.detail) if exc.detail else "HTTP error.",
        status_code=exc.status_code,
        trace_id=trace_id,
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    trace_id = getattr(request.state, "trace_id", None)
    return _envelope(
        code="validation_error",
        message="Request validation failed.",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        trace_id=trace_id,
        details={"errors": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", None)
    log.exception("unhandled_exception", extra={"path": request.url.path, "trace_id": trace_id})
    return _envelope(
        code="internal_error",
        message="An unexpected error occurred.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        trace_id=trace_id,
    )


def register_exception_handlers(app) -> None:
    app.add_exception_handler(TrustScanError, trustscan_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
