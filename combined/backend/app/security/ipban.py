"""IP ban list — admin-controlled runtime blocklist.

Bans are stored in the cache so they apply across workers and survive a
restart (when Redis is configured). Bans support an optional TTL for
progressive escalation (e.g. 5 min -> 1 hour -> permanent).
"""
from __future__ import annotations

import ipaddress
from typing import Optional

from app.cache.redis import cache


_BAN_KEY = "ts:ipban:{ip}"
_BAN_INDEX = "ts:ipban:index"


def _normalise(ip: str) -> Optional[str]:
    try:
        return str(ipaddress.ip_address(ip))
    except ValueError:
        return None


async def ban(ip: str, *, reason: str = "manual", ttl: Optional[int] = None) -> bool:
    """Ban an IP. ``ttl=None`` means permanent (7-day effective max per cache)."""
    normalised = _normalise(ip)
    if not normalised:
        return False
    await cache.set_json(
        _BAN_KEY.format(ip=normalised),
        {"ip": normalised, "reason": reason},
        ttl=ttl or 60 * 60 * 24 * 7,
    )
    return True


async def unban(ip: str) -> bool:
    normalised = _normalise(ip)
    if not normalised:
        return False
    await cache.delete(_BAN_KEY.format(ip=normalised))
    return True


async def is_banned(ip: str) -> bool:
    normalised = _normalise(ip)
    if not normalised:
        return False
    val = await cache.get_json(_BAN_KEY.format(ip=normalised))
    return bool(val)


async def reason_for(ip: str) -> Optional[str]:
    normalised = _normalise(ip)
    if not normalised:
        return None
    val = await cache.get_json(_BAN_KEY.format(ip=normalised))
    if not val:
        return None
    return val.get("reason")
