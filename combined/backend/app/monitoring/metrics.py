"""Lightweight in-memory metrics registry (Prometheus-ready shape).

Exposes counters/gauges as JSON at /api/v1/admin/metrics. For production,
replace with ``prometheus_client`` and expose /metrics directly.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: dict[str, float] = defaultdict(float)
        self._gauges: dict[str, float] = defaultdict(float)
        self._lock = asyncio.Lock()

    async def incr(self, name: str, amount: float = 1.0) -> None:
        async with self._lock:
            self._counters[name] += amount

    async def set(self, name: str, value: float) -> None:
        async with self._lock:
            self._gauges[name] = value

    async def snapshot(self) -> dict:
        async with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }


metrics = MetricsRegistry()
