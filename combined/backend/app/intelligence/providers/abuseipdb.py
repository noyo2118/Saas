"""AbuseIPDB provider — IP abuse confidence score.

Docs: https://docs.abuseipdb.com/#check-endpoint

Stub implementation: active only when ABUSEIPDB_API_KEY is set.
"""
from __future__ import annotations

from app.core.config import settings
from app.intelligence.providers.base import Provider, ProviderVerdict, TargetType
from app.services.http_client import get_client

_ENDPOINT = "https://api.abuseipdb.com/api/v2/check"


class AbuseIPDB(Provider):
    name = "abuseipdb"
    supports: tuple[TargetType, ...] = ("ip",)
    weight = 1.5

    def enabled(self) -> bool:
        return bool(settings.ABUSEIPDB_API_KEY)

    async def lookup(self, target: str, target_type: TargetType) -> ProviderVerdict:
        if not self.enabled():
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error="api_key_missing", confidence=0.0,
            )
        client = await get_client()
        try:
            r = await client.get(
                _ENDPOINT,
                params={"ipAddress": target, "maxAgeInDays": 90},
                headers={"Key": settings.ABUSEIPDB_API_KEY, "Accept": "application/json"},
                timeout=8.0,
            )
        except Exception as exc:  # noqa: BLE001
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error=f"http_error:{type(exc).__name__}", confidence=0.0,
            )

        if r.status_code != 200:
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error=f"http_{r.status_code}", confidence=0.0,
            )
        data = (r.json() or {}).get("data") or {}
        confidence_score = data.get("abuseConfidenceScore", 0)
        return ProviderVerdict(
            provider=self.name,
            target=target,
            target_type=target_type,
            malicious=confidence_score >= 50,
            score=float(confidence_score),
            confidence=0.9,
            categories=[str(c) for c in data.get("usageType", [])] if data.get("usageType") else [],
            raw=data,
        )
