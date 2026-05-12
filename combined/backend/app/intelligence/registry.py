"""Provider registry — single source of truth for enabled intelligence feeds."""
from __future__ import annotations

from functools import lru_cache

from app.intelligence.providers.abuseipdb import AbuseIPDB
from app.intelligence.providers.base import Provider, TargetType
from app.intelligence.providers.google_safe_browsing import GoogleSafeBrowsing
from app.intelligence.providers.ipqs import IPQualityScore
from app.intelligence.providers.scamalytics import Scamalytics

_ALL: list[Provider] = [
    GoogleSafeBrowsing(),
    AbuseIPDB(),
    IPQualityScore(),
    Scamalytics(),
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
