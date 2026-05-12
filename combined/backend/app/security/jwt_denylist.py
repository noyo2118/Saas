"""JWT denylist — make logout actually invalidate an access token.

Short-lived access tokens are hard to revoke. The standard mitigation is to
keep a small cache of revoked ``jti`` claims until their natural expiry, and
check every incoming token against that denylist.

Works with both the Redis and in-memory cache backends. Revocation survives
a restart when backed by Redis.
"""
from __future__ import annotations

from app.cache.redis import cache


def _key(jti: str) -> str:
    return f"ts:jwt:revoked:{jti}"


async def revoke(jti: str, ttl_seconds: int) -> None:
    """Mark a JWT as revoked until its natural expiry."""
    if not jti or ttl_seconds <= 0:
        return
    await cache.set_json(_key(jti), {"revoked": True}, ttl=ttl_seconds)


async def is_revoked(jti: str) -> bool:
    if not jti:
        return False
    val = await cache.get_json(_key(jti))
    return bool(val)
