"""Google Safe Browsing v4 — URL / domain reputation.

Docs: https://developers.google.com/safe-browsing/v4/lookup-api

The API key is optional; when missing, the provider reports ``enabled=False``
and is skipped by the aggregator.
"""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.intelligence.providers.base import Provider, ProviderVerdict, TargetType
from app.services.http_client import get_client
from app.telemetry.logger import get_logger

log = get_logger(__name__)

_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


class GoogleSafeBrowsing(Provider):
    name = "google_safe_browsing"
    supports: tuple[TargetType, ...] = ("url", "domain")
    weight = 2.0  # trusted source

    def enabled(self) -> bool:
        return bool(settings.GOOGLE_SAFE_BROWSING_API_KEY)

    async def lookup(self, target: str, target_type: TargetType) -> ProviderVerdict:
        if not self.enabled():
            return ProviderVerdict(
                provider=self.name,
                target=target,
                target_type=target_type,
                error="api_key_missing",
                confidence=0.0,
            )

        # Safe Browsing expects a URL; prepend https:// for bare domains.
        url = target if target_type == "url" else (
            target if target.startswith("http") else f"https://{target}"
        )

        payload = {
            "client": {
                "clientId": settings.APP_NAME.lower(),
                "clientVersion": settings.APP_VERSION,
            },
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                    "POTENTIALLY_HARMFUL_APPLICATION",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }

        client = await get_client()
        try:
            r = await client.post(
                _ENDPOINT,
                params={"key": settings.GOOGLE_SAFE_BROWSING_API_KEY},
                json=payload,
                timeout=8.0,
            )
        except httpx.HTTPError as exc:
            log.warning("gsb_error", extra={"err": str(exc)})
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error=f"http_error:{type(exc).__name__}", confidence=0.0,
            )

        if r.status_code != 200:
            return ProviderVerdict(
                provider=self.name, target=target, target_type=target_type,
                error=f"http_{r.status_code}", confidence=0.0,
                raw={"body": r.text[:200]},
            )

        data = r.json() or {}
        matches = data.get("matches") or []
        malicious = len(matches) > 0
        categories = sorted({m.get("threatType", "") for m in matches if m.get("threatType")})

        return ProviderVerdict(
            provider=self.name,
            target=target,
            target_type=target_type,
            malicious=malicious,
            score=100.0 if malicious else 0.0,
            confidence=0.95 if malicious else 0.75,
            categories=categories,
            raw=data,
        )
