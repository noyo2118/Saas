"""Security response headers — hardened OWASP-grade defaults.

Covers:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY (defence in depth with CSP frame-ancestors)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: disable every sensor / payment / autoplay surface
    - Cross-Origin-Opener-Policy / Resource-Policy / Embedder-Policy
    - Strict-Transport-Security on HTTPS (1 year, includeSubDomains, preload)
    - Content-Security-Policy: strict default-src 'none', no inline scripts
    - Cache-Control: no-store on JSON API responses
"""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Strict CSP for a JSON-only API. If the backend ever serves HTML it should
# be split per-route.
_API_CSP = (
    "default-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'; "
    "form-action 'none'; "
    "upgrade-insecure-requests"
)

_BASE_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": (
        "accelerometer=(), autoplay=(), camera=(), clipboard-read=(), "
        "clipboard-write=(), cross-origin-isolated=(), display-capture=(), "
        "document-domain=(), encrypted-media=(), fullscreen=(), geolocation=(), "
        "gyroscope=(), hid=(), identity-credentials-get=(), idle-detection=(), "
        "magnetometer=(), microphone=(), midi=(), payment=(), picture-in-picture=(), "
        "publickey-credentials-get=(), screen-wake-lock=(), serial=(), "
        "sync-xhr=(), usb=(), web-share=(), xr-spatial-tracking=()"
    ),
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
    "Cross-Origin-Embedder-Policy": "require-corp",
    "Content-Security-Policy": _API_CSP,
    # Anti-enumeration / fingerprinting
    "X-Permitted-Cross-Domain-Policies": "none",
    "X-DNS-Prefetch-Control": "off",
    # Hide implementation details
    "Server": "TrustScan",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for k, v in _BASE_HEADERS.items():
            response.headers.setdefault(k, v)

        # HSTS only over HTTPS (never send on plain HTTP — pointless and may cause issues)
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )

        # Default: JSON API responses should never be cached by intermediaries
        # Exclude PDF downloads + websocket handshake.
        path = request.url.path
        ctype = response.headers.get("content-type", "")
        is_pdf = "application/pdf" in ctype
        if not is_pdf:
            response.headers.setdefault("Cache-Control", "no-store, max-age=0")
            response.headers.setdefault("Pragma", "no-cache")

        return response
