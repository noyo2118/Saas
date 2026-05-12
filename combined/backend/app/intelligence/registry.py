"""Provider registry — single source of truth for enabled intelligence feeds.

Every provider in this list uses a **free** API tier:
    - GoogleSafeBrowsing: free with API key (10k req/day)
    - AbuseIPDB:          free tier 1,000 checks/day
    - IPQualityScore:     free tier 5,000 lookups/month

Paid-only feeds (e.g. Scamalytics) are intentionally excluded.
Add a provider by subclassing ``Provider`` and appending to ``_ALL``.
"""
from __future__ import annotations

from functools import lru_cache

from app.intelligence.providers.abuseipdb import AbuseIPDB
from app.intelligence.providers.base import Provider, TargetType
from app.intelligence.providers.google_safe_browsing import GoogleSafeBrowsing
from app.intelligence.providers.ipqs import IPQualityScore

_ALL: list[Provider] = [
    GoogleSafeBrowsing(),
    AbuseIPDB(),
    IPQualityScore(),
]


@lru_cache(maxsize=8)
def providers_for(target_type: TargetType) -> tuple[Provider, ...]:
    return tuple(
        p for p in _ALL
        if target_type in p.supports and p.enabled()
    )


def all_providers_meta() -> list[dict]:
    """Introspection helper — show which providers are active."""
    return [
        {
            "name": p.name,
            "supports": list(p.supports),
            "weight": p.weight,
            "enabled": p.enabled(),
        }
        for p in _ALL
    ]
