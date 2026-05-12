"""URL / website analysis engine.

Inspects:
    - HTTPS enforcement & scheme
    - Full TLS/SSL handshake & certificate details
    - HTTP response headers (CSP, HSTS, X-Frame-Options, ...)
    - Redirect chain (with intra-chain host changes)
    - Server fingerprint / response time
    - Suspicious script / iframe / form patterns in HTML body
"""
from __future__ import annotations

import asyncio
import re
import socket
import ssl
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.security.ssrf import assert_safe_url
from app.services.http_client import get_client
from app.telemetry.logger import get_logger

log = get_logger(__name__)

SECURITY_HEADERS = [
    "content-security-policy",
    "content-security-policy-report-only",
    "x-frame-options",
    "strict-transport-security",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
    "x-xss-protection",
    "cross-origin-opener-policy",
    "cross-origin-embedder-policy",
]

SUSPICIOUS_HTML_PATTERNS = [
    (re.compile(r"<iframe[^>]+src=[\"'](?:https?:)?//[^\"']+", re.I), "iframe_external"),
    (re.compile(r"eval\s*\(", re.I), "eval_call"),
    (re.compile(r"document\.write\s*\(", re.I), "document_write"),
    (re.compile(r"window\.location\s*=", re.I), "js_redirect"),
    (re.compile(r"atob\s*\(", re.I), "base64_decode"),
    (re.compile(r"<input[^>]+type=[\"']password", re.I), "password_field"),
    (re.compile(r"<form[^>]+action=[\"']https?://", re.I), "external_form"),
]


def _parse_ssl_cert(hostname: str) -> dict[str, Any]:
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert() or {}
                version = ssock.version()
                cipher = ssock.cipher()

        expires_str = cert.get("notAfter", "")
        days_left = None
        try:
            expires_dt = datetime.strptime(expires_str, "%b %d %H:%M:%S %Y %Z")
            days_left = (expires_dt - datetime.now(timezone.utc).replace(tzinfo=None)).days
        except Exception:  # noqa: BLE001
            pass

        issuer = {k: v for item in cert.get("issuer", []) for k, v in item}
        subject = {k: v for item in cert.get("subject", []) for k, v in item}

        san = [name for (typ, name) in cert.get("subjectAltName", []) if typ == "DNS"]

        return {
            "valid": True,
            "issuer": issuer.get("organizationName") or issuer.get("commonName") or "Unknown",
            "issuer_cn": issuer.get("commonName"),
            "subject_cn": subject.get("commonName", hostname),
            "san": san[:20],
            "expires": expires_str,
            "days_left": days_left,
            "tls_version": version,
            "cipher": cipher[0] if cipher else None,
            "expired": (days_left is not None and days_left <= 0),
            "expiring_soon": (days_left is not None and 0 < days_left <= 30),
        }
    except Exception as exc:  # noqa: BLE001
        return {"valid": False, "error": str(exc)}


async def analyze_url(url: str) -> dict[str, Any]:
    """End-to-end URL/website inspection. Returns a structured dict."""
    await assert_safe_url(url)
    hostname = urlparse(url).hostname or ""
    client = await get_client()
    started = time.perf_counter()

    result: dict[str, Any] = {
        "url": url,
        "hostname": hostname,
        "https": url.startswith("https://"),
        "status_code": None,
        "http_version": None,
        "response_time_ms": None,
        "server": None,
        "final_url": None,
        "redirects": 0,
        "redirect_chain": [],
        "cross_host_redirect": False,
        "headers": {},
        "header_flags": {
            "csp": False, "xframe": False, "hsts": False,
            "xcontent": False, "referrer": False, "permissions": False,
        },
        "body_patterns": [],
        "body_length": 0,
        "error": None,
    }

    try:
        r = await client.get(
            url,
            headers={"User-Agent": settings.HTTP_USER_AGENT, "Accept-Language": "en"},
            follow_redirects=True,
            timeout=settings.HTTP_TIMEOUT,
        )
        result["status_code"] = r.status_code
        result["http_version"] = getattr(r, "http_version", None)
        result["redirects"] = len(r.history)
        result["final_url"] = str(r.url)

        seen_hosts = {hostname}
        for resp in r.history:
            hop_host = urlparse(str(resp.url)).hostname
            seen_hosts.add(hop_host or "")
            result["redirect_chain"].append({
                "url": str(resp.url), "status": resp.status_code, "host": hop_host,
            })
        result["cross_host_redirect"] = len(seen_hosts) > 1

        headers_lc = {k.lower(): v for k, v in r.headers.items()}
        for h in SECURITY_HEADERS:
            if h in headers_lc:
                result["headers"][h] = headers_lc[h][:512]
        result["server"] = headers_lc.get("server") or headers_lc.get("x-powered-by") or "Unknown"
        result["header_flags"] = {
            "csp": "content-security-policy" in headers_lc or "content-security-policy-report-only" in headers_lc,
            "xframe": "x-frame-options" in headers_lc,
            "hsts": "strict-transport-security" in headers_lc,
            "xcontent": "x-content-type-options" in headers_lc,
            "referrer": "referrer-policy" in headers_lc,
            "permissions": "permissions-policy" in headers_lc,
        }

        # body patterns — only inspect first 256 KiB
        body = r.text[:262_144] if r.text else ""
        result["body_length"] = len(r.text or "")
        found = []
        for rx, label in SUSPICIOUS_HTML_PATTERNS:
            if rx.search(body):
                found.append(label)
        result["body_patterns"] = found

    except httpx.TimeoutException:
        result["error"] = "timeout"
    except httpx.HTTPError as exc:
        result["error"] = f"http_error:{type(exc).__name__}"
    except Exception as exc:  # noqa: BLE001
        result["error"] = str(exc)[:240]

    result["response_time_ms"] = int((time.perf_counter() - started) * 1000)

    # SSL + reverse DNS concurrently in threads
    ssl_info, ip = await asyncio.gather(
        asyncio.to_thread(_parse_ssl_cert, hostname) if hostname else _noop({}),
        asyncio.to_thread(_resolve_a, hostname) if hostname else _noop(None),
    )
    result["ssl"] = ssl_info
    result["ip"] = ip
    return result


def _resolve_a(hostname: str) -> str | None:
    try:
        return socket.gethostbyname(hostname)
    except Exception:  # noqa: BLE001
        return None


async def _noop(v):
    return v
