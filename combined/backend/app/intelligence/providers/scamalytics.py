"""Scamalytics provider — IP fraud score.

Docs: https://scamalytics.com/ip/api

Active only when SCAMALYTICS_API_KEY is set.
"""
from __future__ import annotations

from app.core.config import settings
from app.intelligence.providers.base import Provider, ProviderVerdict, TargetType
from app.services.http_client import get_client


class Scamalytics(Provider):
    name = "scamalytics"
    supports: tuple[TargetType, ...] = ("ip",)
    weight = 1.0

    def enabled(self) -> bool:
        return bool(settings.SCAMALYTICS_API_KEY)

    async def lookup(self, target: str, target_type: TargetType) -> ProviderVerdict:
        if not self.enabled():
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error="api_key_missing", confidence=0.0,
            )
        client = await get_client()
        try:
            r = await client.get(
                "https://api11.scamalytics.com/v1/ip",
                params={"key": settings.SCAMALYTICS_API_KEY, "ip": target},
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
        data = r.json() or {}
        risk = data.get("score", 0)
        risk_text = str(data.get("risk", "unknown")).lower()
        return ProviderVerdict(
            provider=self.name,
            target=target,
            target_type=target_type,
            malicious=risk_text in {"high", "very_high"},
            score=float(risk),
            confidence=0.75,
            categories=[risk_text],
            raw=data,
        )
