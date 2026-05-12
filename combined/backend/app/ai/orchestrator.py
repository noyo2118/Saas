"""AI orchestrator — picks the first enabled provider, falls back gracefully."""
from __future__ import annotations

from typing import Any

from app.ai.prompts import fallback_report
from app.ai.providers.base import AIResponse
from app.ai.providers.claude import ClaudeAI
from app.ai.providers.google import GoogleAI
from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.telemetry.logger import get_logger

log = get_logger(__name__)

_PROVIDERS = [GoogleAI(), ClaudeAI()]


def _build_context(scan_payload: dict[str, Any]) -> dict[str, Any]:
    url = scan_payload.get("url") or {}
    domain = scan_payload.get("domain") or {}
    reputation = scan_payload.get("reputation") or {}
    phishing = scan_payload.get("phishing") or {}
    scoring = scan_payload.get("scoring") or {}
    return {
        "target": scan_payload.get("target"),
        "target_type": scan_payload.get("target_type"),
        "trust_score": scoring.get("trust_score"),
        "verdict": scoring.get("verdict"),
        "fraud_probability": scoring.get("fraud_probability"),
        "threat_level": scoring.get("threat_level"),
        "https": url.get("https"),
        "ssl_valid": (url.get("ssl") or {}).get("valid"),
        "age_days": (domain.get("whois") or {}).get("age_days"),
        "rep_malicious": reputation.get("malicious"),
        "rep_categories": reputation.get("categories") or [],
        "phishing_score": phishing.get("score"),
        "indicators": scoring.get("indicators") or [],
    }


async def generate_report(scan_id: str, scan_payload: dict[str, Any]) -> AIResponse:
    """Produce a narrative AI report for a scan. Cached by scan id."""
    key = ns.ai(scan_id)
    cached = await cache.get_json(key)
    if cached:
        return AIResponse(**cached)

    context = _build_context(scan_payload)
    for provider in _PROVIDERS:
        if not provider.enabled():
            continue
        resp = await provider.generate(context)
        if not resp.error and resp.summary:
            payload = resp.__dict__
            await cache.set_json(key, payload, ttl=settings.CACHE_AI_TTL)
            return resp
        log.info("ai_provider_skipped", extra={"provider": provider.name, "err": resp.error})

    # fallback
    fb = fallback_report(context)
    resp = AIResponse(
        provider="fallback",
        model=None,
        summary=fb["summary"],
        exec_summary=fb["exec_summary"],
        risk_description=fb["risk_description"],
        remediation=fb["remediation"],
    )
    await cache.set_json(key, resp.__dict__, ttl=settings.CACHE_AI_TTL // 4)
    return resp
