"""Shared async HTTPX client with sane defaults and SSRF-aware helpers."""
from __future__ import annotations

from typing import Optional

import httpx

from app.core.config import settings

_client: Optional[httpx.AsyncClient] = None


def _default_headers() -> dict:
    return {
        "User-Agent": settings.HTTP_USER_AGENT,
        "Accept": "*/*",
    }


async def get_client() -> httpx.AsyncClient:
    """Return a long-lived AsyncClient with connection pooling."""
    global _client
    if _client is None or _client.is_closed:
        limits = httpx.Limits(
            max_keepalive_connections=20,
            max_connections=100,
            keepalive_expiry=30.0,
        )
        timeout = httpx.Timeout(
            connect=settings.HTTP_TIMEOUT,
            read=settings.HTTP_TIMEOUT,
            write=settings.HTTP_TIMEOUT,
            pool=settings.HTTP_TIMEOUT,
        )
        _client = httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            follow_redirects=False,
            headers=_default_headers(),
            http2=False,
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
