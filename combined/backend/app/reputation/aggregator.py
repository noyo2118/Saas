"""Intelligence aggregator.

Fans out to every enabled provider for a target, gathers their verdicts
in parallel, and returns a merged weighted-confidence summary.
"""
from __future__ import annotations

import asyncio
from typing import Any

from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.intelligence.providers.base import Provider, ProviderVerdict, TargetType
from app.intelligence.registry import providers_for
from app.telemetry.logger import get_logger

log = get_logger(__name__)


async def _safe_lookup(p: Provider, target: str, tt: TargetType) -> ProviderVerdict:
    key = ns.reputation(p.name, target)
    cached = await cache.get_json(key)
    if cached is not None:
        return ProviderVerdict(**cached)  # type: ignore[arg-type]
    try:
        v = await asyncio.wait_for(p.lookup(target, tt), timeout=10.0)
    except asyncio.TimeoutError:
        return ProviderVerdict(
            provider=p.name, target=target, target_type=tt,
            error="timeout", confidence=0.0,
        )
    except Exception as exc:  # noqa: BLE001
        log.warning("provider_error", extra={"provider": p.name, "err": str(exc)[:160]})
        return ProviderVerdict(
            provider=p.name, target=target, target_type=tt,
            error=f"{type(exc).__name__}", confidence=0.0,
        )

    payload = {
        "provider": v.provider, "target": v.target, "target_type": v.target_type,
        "malicious": v.malicious, "score": v.score, "confidence": v.confidence,
        "categories": v.categories, "raw": v.raw, "error": v.error,
    }
    await cache.set_json(key, payload, ttl=settings.CACHE_REPUTATION_TTL)
    return v


async def _aggregate(target: str, target_type: TargetType) -> dict[str, Any]:
    providers = providers_for(target_type)
    if not providers:
        return {
            "providers": [],
            "malicious": None,
            "score": None,
            "confidence": 0.0,
            "categories": [],
            "note": "no_providers_enabled",
        }
    verdicts = await asyncio.gather(*(_safe_lookup(p, target, target_type) for p in providers))

    # Weighted merge
    total_w = 0.0
    weighted_score = 0.0
    malicious_votes = 0.0
    total_votes = 0.0
    categories: set[str] = set()
    per_provider: list[dict[str, Any]] = []

    weights = {p.name: p.weight for p in providers}

    for v in verdicts:
        per_provider.append({
            "provider": v.provider,
            "malicious": v.malicious,
            "score": v.score,
            "confidence": v.confidence,
            "categories": v.categories,
            "error": v.error,
        })
        if not v.is_known():
            continue
        w = weights.get(v.provider, 1.0) * v.confidence
        if v.score is not None:
            weighted_score += v.score * w
            total_w += w
        if v.malicious is not None:
            total_votes += w
            if v.malicious:
                malicious_votes += w
        for c in v.categories:
            categories.add(c)

    merged_score = round(weighted_score / total_w, 2) if total_w > 0 else None
    merged_malicious = None
    if total_votes > 0:
        merged_malicious = (malicious_votes / total_votes) >= 0.5
    confidence = min(1.0, total_w / max(1.0, sum(weights.values())))

    return {
        "providers": per_provider,
        "malicious": merged_malicious,
        "score": merged_score,
        "confidence": round(confidence, 3),
        "categories": sorted(categories),
    }


async def fetch_url_reputation(url: str) -> dict[str, Any]:
    return await _aggregate(url, "url")


async def fetch_domain_reputation(domain: str) -> dict[str, Any]:
    return await _aggregate(domain, "domain")


async def fetch_ip_reputation(ip: str) -> dict[str, Any]:
    agg = await _aggregate(ip, "ip")
    # Infer vpn/proxy/tor from provider raw payloads when available.
    vpt = {"vpn": False, "proxy": False, "tor": False}
    for prov in agg.get("providers", []):
        raw = prov.get("raw") if isinstance(prov, dict) else None
        if isinstance(raw, dict):
            for k in ("vpn", "proxy", "tor"):
                if raw.get(k):
                    vpt[k] = True
    agg["vpn_proxy_tor"] = vpt
    agg["abuse_score"] = agg.get("score")
    return agg


async def fetch_email_reputation(email: str) -> dict[str, Any]:
    return await _aggregate(email, "email")
