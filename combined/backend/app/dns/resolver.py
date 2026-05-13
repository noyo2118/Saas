"""DNS resolution helpers — pure stdlib, async-safe (runs in threads).

Intentionally dependency-free so the project doesn't require ``dnspython``.
If ``dnspython`` is installed we'll use it for MX/TXT; otherwise we fall
back to ``socket.getaddrinfo`` for A/AAAA only.
"""
from __future__ import annotations

import asyncio
import socket
from typing import Any

try:  # optional upgrade
    import dns.resolver  # type: ignore
    _HAS_DNSPY = True
except Exception:  # noqa: BLE001
    _HAS_DNSPY = False

from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings


def _sync_a(domain: str) -> list[str]:
    try:
        infos = socket.getaddrinfo(domain, None, type=socket.SOCK_STREAM)
        return sorted({info[4][0] for info in infos})
    except Exception:  # noqa: BLE001
        return []


def _sync_mx(domain: str) -> list[str]:
    if not _HAS_DNSPY:
        return []
    try:
        ans = dns.resolver.resolve(domain, "MX", lifetime=5)
        return sorted({r.exchange.to_text().rstrip(".") for r in ans})
    except Exception:  # noqa: BLE001
        return []


def _sync_txt(domain: str) -> list[str]:
    if not _HAS_DNSPY:
        return []
    try:
        ans = dns.resolver.resolve(domain, "TXT", lifetime=5)
        return ["".join(b.decode("utf-8", "ignore") for b in r.strings) for r in ans]
    except Exception:  # noqa: BLE001
        return []


def _sync_ns(domain: str) -> list[str]:
    if not _HAS_DNSPY:
        return []
    try:
        ans = dns.resolver.resolve(domain, "NS", lifetime=5)
        return sorted({r.target.to_text().rstrip(".") for r in ans})
    except Exception:  # noqa: BLE001
        return []


async def resolve_all(domain: str) -> dict[str, Any]:
    """Return A, MX, NS, TXT and parse SPF/DKIM/DMARC flags."""
    key = ns.dns("all", domain)
    cached = await cache.get_json(key)
    if cached is not None:
        return cached

    a, mx, ns_records, txt = await asyncio.gather(
        asyncio.to_thread(_sync_a, domain),
        asyncio.to_thread(_sync_mx, domain),
        asyncio.to_thread(_sync_ns, domain),
        asyncio.to_thread(_sync_txt, domain),
    )

    spf = next((t for t in txt if t.lower().startswith("v=spf1")), None)
    dmarc_txt = await asyncio.to_thread(_sync_txt, f"_dmarc.{domain}")
    dmarc = next((t for t in dmarc_txt if t.lower().startswith("v=dmarc1")), None)
    dkim_default = await asyncio.to_thread(_sync_txt, f"default._domainkey.{domain}")
    dkim = next((t for t in dkim_default if "dkim" in t.lower() or "p=" in t.lower()), None)

    result = {
        "a": a,
        "mx": mx,
        "ns": ns_records,
        "txt": txt[:20],
        "spf": spf,
        "dmarc": dmarc,
        "dkim_default_selector": dkim,
        "has_email_config": bool(mx and spf),
    }
    await cache.set_json(key, result, ttl=settings.CACHE_DNS_TTL)
    return result
