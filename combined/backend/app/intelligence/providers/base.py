"""Reputation / intelligence provider base classes.

A ``Provider`` is anything that can answer a lookup for a target and return
a normalised ``ProviderVerdict``. The aggregator fans out to every enabled
provider, merges their verdicts with confidence weighting and returns.

Add a new provider by subclassing ``Provider`` and registering it in
``app.intelligence.registry``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

TargetType = Literal["url", "domain", "ip", "email"]


@dataclass(slots=True)
class ProviderVerdict:
    """Normalised result from a single provider."""

    provider: str
    target: str
    target_type: TargetType
    malicious: Optional[bool] = None  # True/False/None (= unknown)
    score: Optional[float] = None  # 0..100, higher = worse
    confidence: float = 0.5  # 0..1
    categories: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def is_known(self) -> bool:
        return self.malicious is not None or self.score is not None


class Provider:
    """Abstract provider — must be cheap to instantiate."""

    name: str = "base"
    supports: tuple[TargetType, ...] = ()
    weight: float = 1.0  # relative voting weight when aggregating

    def enabled(self) -> bool:
        """Override to check API keys / configuration."""
        return True

    async def lookup(self, target: str, target_type: TargetType) -> ProviderVerdict:
        raise NotImplementedError
