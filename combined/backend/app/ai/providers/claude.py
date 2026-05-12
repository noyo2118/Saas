"""Claude (via Puter.js) provider — free AI relay.

Puter.com exposes Anthropic's Messages API under its own gateway. A single
``PUTER_AUTH_TOKEN`` enables Claude Sonnet for free through the existing
browser-captured auth token, no Anthropic billing, no API key management.

Docs: https://docs.puter.com/ai/chat/
Endpoint: https://api.puter.com/puterai/anthropic/v1/messages

Set ``PUTER_AUTH_TOKEN`` in your ``.env`` to enable. When the token is
absent the provider reports disabled and the orchestrator falls back to
Google Gemini or the deterministic rule-based report.
"""
from __future__ import annotations

from app.ai.prompts import build_prompt, parse_response
from app.ai.providers.base import AIProvider, AIResponse
from app.core.config import settings
from app.services.http_client import get_client
from app.telemetry.logger import get_logger

log = get_logger(__name__)

_PUTER_ENDPOINT = "https://api.puter.com/puterai/anthropic/v1/messages"


class ClaudeAI(AIProvider):
    """Claude via Puter.js — free tier, same Claude model quality."""

    name = "claude"

    def enabled(self) -> bool:
        return bool(settings.PUTER_AUTH_TOKEN)

    async def generate(self, context: dict) -> AIResponse:
        if not self.enabled():
            return AIResponse(provider=self.name, error="puter_token_missing")

        prompt = build_prompt(context)
        client = await get_client()
        try:
            r = await client.post(
                _PUTER_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {settings.PUTER_AUTH_TOKEN}",
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.AI_MODEL_CLAUDE,
                    "max_tokens": 700,
                    "temperature": 0.2,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30.0,
            )
        except Exception as exc:  # noqa: BLE001
            return AIResponse(provider=self.name, error=f"http_error:{type(exc).__name__}")

        if r.status_code != 200:
            log.warning("puter_ai_non_200", extra={"status": r.status_code})
            return AIResponse(
                provider=self.name,
                model=settings.AI_MODEL_CLAUDE,
                error=f"http_{r.status_code}",
            )

        data = r.json() or {}
        try:
            text = data["content"][0]["text"]
        except (KeyError, IndexError, TypeError):
            return AIResponse(provider=self.name, error="empty_response")

        parsed = parse_response(text)
        usage = data.get("usage") or {}
        return AIResponse(
            provider=self.name,
            model=settings.AI_MODEL_CLAUDE,
            summary=parsed.get("summary"),
            exec_summary=parsed.get("exec_summary"),
            risk_description=parsed.get("risk_description"),
            remediation=parsed.get("remediation"),
            tokens_in=usage.get("input_tokens"),
            tokens_out=usage.get("output_tokens"),
        )
