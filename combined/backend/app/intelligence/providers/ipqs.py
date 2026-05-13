"""IPQualityScore provider — IP + URL fraud / VPN / proxy detection.

Docs: https://www.ipqualityscore.com/documentation/proxy-detection-api

Active only when IPQS_API_KEY is set.
"""
from __future__ import annotations

from app.core.config import settings
from app.intelligence.providers.base import Provider, ProviderVerdict, TargetType
from app.services.http_client import get_client


class IPQualityScore(Provider):
    name = "ipqualityscore"
    supports: tuple[TargetType, ...] = ("ip", "url", "email")
    weight = 1.5

    def enabled(self) -> bool:
        return bool(settings.IPQS_API_KEY)

    async def lookup(self, target: str, target_type: TargetType) -> ProviderVerdict:
        if not self.enabled():
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error="api_key_missing", confidence=0.0,
            )
        key = settings.IPQS_API_KEY
        if target_type == "ip":
            url = f"https://www.ipqualityscore.com/api/json/ip/{key}/{target}"
        elif target_type == "email":
            url = f"https://www.ipqualityscore.com/api/json/email/{key}/{target}"
        else:
            url = f"https://www.ipqualityscore.com/api/json/url/{key}/{target}"

        client = await get_client()
        try:
            r = await client.get(url, timeout=8.0)
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
        data = r.json() or {}
        fraud_score = data.get("fraud_score") or data.get("risk_score") or 0
        return ProviderVerdict(
            provider=self.name,
            target=target,
            target_type=target_type,
            malicious=bool(data.get("malicious") or fraud_score >= 85),
            score=float(fraud_score),
            confidence=0.85,
            raw=data,
        )
