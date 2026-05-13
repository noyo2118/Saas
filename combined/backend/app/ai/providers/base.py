"""AI provider abstraction — single ``generate`` contract.

Each provider returns a ``AIResponse`` with natural-language fields. When no
provider is configured, the orchestrator falls back to a deterministic
rule-based generator so the API always returns something useful.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class AIResponse:
    provider: str
    model: Optional[str] = None
    summary: Optional[str] = None
    exec_summary: Optional[str] = None
    risk_description: Optional[str] = None
    remediation: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    error: Optional[str] = None


class AIProvider:
    name: str = "base"

    def enabled(self) -> bool:
        return False

    async def generate(self, context: dict) -> AIResponse:  # noqa: D401
        raise NotImplementedError
