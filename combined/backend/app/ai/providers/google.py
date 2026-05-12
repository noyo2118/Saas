"""Google Gemini AI provider via the REST generateContent endpoint.

Docs: https://ai.google.dev/api/generate-content
Enabled when GOOGLE_AI_API_KEY is set.
"""
from __future__ import annotations

import json

from app.ai.prompts import build_prompt, parse_response
from app.ai.providers.base import AIProvider, AIResponse
from app.core.config import settings
from app.services.http_client import get_client


class GoogleAI(AIProvider):
    name = "google"

    def enabled(self) -> bool:
        return bool(settings.GOOGLE_AI_API_KEY)

    async def generate(self, context: dict) -> AIResponse:
        if not self.enabled():
            return AIResponse(provider=self.name, error="api_key_missing")

        prompt = build_prompt(context)
        client = await get_client()
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.AI_MODEL_GOOGLE}:generateContent"
        )
        try:
            r = await client.post(
                url,
                params={"key": settings.GOOGLE_AI_API_KEY},
                json={
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 700},
                },
                timeout=20.0,
            )
        except Exception as exc:  # noqa: BLE001
            return AIResponse(provider=self.name, error=f"http_error:{type(exc).__name__}")

        if r.status_code != 200:
            return AIResponse(
                provider=self.name,
                model=settings.AI_MODEL_GOOGLE,
                error=f"http_{r.status_code}",
            )

        data = r.json() or {}
        text = ""
        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            return AIResponse(provider=self.name, error="empty_response")

        parsed = parse_response(text)
        usage = data.get("usageMetadata") or {}
        return AIResponse(
            provider=self.name,
            model=settings.AI_MODEL_GOOGLE,
            summary=parsed.get("summary"),
            exec_summary=parsed.get("exec_summary"),
            risk_description=parsed.get("risk_description"),
            remediation=parsed.get("remediation"),
            tokens_in=usage.get("promptTokenCount"),
            tokens_out=usage.get("candidatesTokenCount"),
        )
