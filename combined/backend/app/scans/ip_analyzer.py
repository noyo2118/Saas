"""IP intelligence — geolocation + reputation aggregation."""
from __future__ import annotations

import asyncio
from typing import Any

from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.security.ssrf import validate_ip_target
from app.services.http_client import get_client


async def _geo_lookup(ip: str) -> dict[str, Any]:
    """Free IP geolocation via ipapi.co (no key required)."""
    key = ns.dns("geo", ip)
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    client = await get_client()
    try:
        r = await client.get(f"https://ipapi.co/{ip}/json/", timeout=6.0)
        if r.status_code == 200:
            data = r.json()
            if "error" in data:
                return {}
            out = {
                "country": data.get("country_name"),
                "country_code": data.get("country_code"),
                "region": data.get("region"),
                "city": data.get("city"),
                "org": data.get("org"),
                "asn": data.get("asn"),
                "timezone": data.get("timezone"),
            }
            await cache.set_json(key, out, ttl=settings.CACHE_DNS_TTL * 6)
            return out
    except Exception:  # noqa: BLE001
        pass
    return {}


async def analyze_ip(ip: str) -> dict[str, Any]:
    """Gather all IP intelligence. Validates the IP is public first."""
    ip = validate_ip_target(ip)

    from app.reputation.aggregator import fetch_ip_reputation

    geo, rep = await asyncio.gather(_geo_lookup(ip), fetch_ip_reputation(ip))

    return {
        "ip": ip,
        "geo": geo,
        "reputation": rep,
        "vpn_proxy_tor": rep.get("vpn_proxy_tor", {}),
        "abuse_score": rep.get("abuse_score"),
    }
