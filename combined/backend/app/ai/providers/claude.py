"""Anthropic Claude provider.

Docs: https://docs.anthropic.com/en/api/messages
Enabled when ANTHROPIC_API_KEY is set.
"""
from __future__ import annotations

from app.ai.prompts import build_prompt, parse_response
from app.ai.providers.base import AIProvider, AIResponse
from app.core.config import settings
from app.services.http_client import get_client


class ClaudeAI(AIProvider):
    name = "claude"

    def enabled(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

    async def generate(self, context: dict) -> AIResponse:
        if not self.enabled():
            return AIResponse(provider=self.name, error="api_key_missing")

        prompt = build_prompt(context)
        client = await get_client()
        try:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.AI_MODEL_CLAUDE,
                    "max_tokens": 700,
                    "temperature": 0.2,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=25.0,
            )
        except Exception as exc:  # noqa: BLE001
            return AIResponse(provider=self.name, error=f"http_error:{type(exc).__name__}")

        if r.status_code != 200:
            return AIResponse(
                provider=self.name,
                model=settings.AI_MODEL_CLAUDE,
                error=f"http_{r.status_code}",
            )

        data = r.json() or {}
        text = ""
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
