"""Brute-force protection for authentication endpoints.

The lockout tracks failures per ``(identity, ip)`` bucket. After
``AUTH_LOCKOUT_THRESHOLD`` failures inside ``AUTH_LOCKOUT_WINDOW_SEC`` we mark
the bucket locked for ``AUTH_LOCKOUT_DURATION_SEC`` seconds. Successful auth
resets the counter.
"""
from __future__ import annotations

import hashlib

from app.cache.redis import cache
from app.core.config import settings
from app.core.exceptions import RateLimitError


def _bucket(identity: str, ip: str | None) -> str:
    key = f"{identity.lower()}|{ip or 'unknown'}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return f"ts:lockout:{digest}"


async def assert_not_locked(identity: str, ip: str | None) -> None:
    key = _bucket(identity, ip)
    row = await cache.get_json(key)
    if not row:
        return
    if row.get("locked"):
        ttl = max(0, await cache.ttl(key))
        raise RateLimitError(
            message="Too many failed attempts. Please try again later.",
            details={"retry_after": ttl},
        )


async def register_failure(identity: str, ip: str | None) -> None:
    key = _bucket(identity, ip)
    row = await cache.get_json(key) or {"count": 0, "locked": False}
    row["count"] = int(row.get("count", 0)) + 1
    if row["count"] >= settings.AUTH_LOCKOUT_THRESHOLD:
        row["locked"] = True
        await cache.set_json(key, row, ttl=settings.AUTH_LOCKOUT_DURATION_SEC)
    else:
        await cache.set_json(key, row, ttl=settings.AUTH_LOCKOUT_WINDOW_SEC)


async def clear_failures(identity: str, ip: str | None) -> None:
    await cache.delete(_bucket(identity, ip))
