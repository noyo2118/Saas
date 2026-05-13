"""Cache backend — Redis when REDIS_URL is set, otherwise a TTL in-memory fallback.

The public API is async and backend-agnostic. All callers use ``cache`` —
the singleton instance — and are unaware of the underlying driver.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any, Optional

import orjson

from app.core.config import settings
from app.telemetry.logger import get_logger

log = get_logger(__name__)


# -------------------------------------------------------------------- in-memory
class _InMemoryBackend:
    """Async-safe TTL dict. Used when Redis is not configured."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, bytes]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[bytes]:
        async with self._lock:
            row = self._store.get(key)
            if not row:
                return None
            expires_at, value = row
            if expires_at and expires_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: bytes, ex: Optional[int] = None) -> None:
        async with self._lock:
            expires_at = time.time() + ex if ex else 0
            self._store[key] = (expires_at, value)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def incr(self, key: str, ex: Optional[int] = None) -> int:
        async with self._lock:
            row = self._store.get(key)
            if row:
                expires_at, value = row
                if expires_at and expires_at < time.time():
                    value = b"0"
                    expires_at = 0
            else:
                value = b"0"
                expires_at = 0
            counter = int(value) + 1
            if not expires_at and ex:
                expires_at = time.time() + ex
            self._store[key] = (expires_at, str(counter).encode())
            return counter

    async def ttl(self, key: str) -> int:
        async with self._lock:
            row = self._store.get(key)
            if not row:
                return -2
            expires_at, _ = row
            if not expires_at:
                return -1
            remaining = int(expires_at - time.time())
            return remaining if remaining > 0 else -2

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        self._store.clear()


# -------------------------------------------------------------------- public
class Cache:
    """Thin async facade over Redis / in-memory. JSON-encodes/decodes by default."""

    def __init__(self) -> None:
        self._backend: Any = None
        self.backend_name: str = "uninitialised"

    # -------------------------------------------------- lifecycle
    async def connect(self) -> None:
        if settings.REDIS_URL:
            try:
                import redis.asyncio as redis  # type: ignore

                client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=False,
                    socket_timeout=3,
                    socket_connect_timeout=3,
                )
                await client.ping()
                self._backend = client
                self.backend_name = "redis"
                return
            except Exception as exc:  # noqa: BLE001
                log.warning("redis_connect_failed", extra={"err": str(exc)})

        self._backend = _InMemoryBackend()
        self.backend_name = "memory"

    async def disconnect(self) -> None:
        if self._backend is None:
            return
        try:
            close = getattr(self._backend, "aclose", None) or getattr(self._backend, "close", None)
            if close:
                res = close()
                if asyncio.iscoroutine(res):
                    await res
        except Exception:  # noqa: BLE001
            pass
        self._backend = None

    # -------------------------------------------------- json helpers
    async def get_json(self, key: str) -> Optional[Any]:
        raw = await self._backend.get(key)
        if raw is None:
            return None
        try:
            return orjson.loads(raw)
        except Exception:  # noqa: BLE001
            return None

    async def set_json(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        payload = orjson.dumps(value, default=str)
        await self._backend.set(key, payload, ex=ttl)

    async def delete(self, key: str) -> None:
        await self._backend.delete(key)

    async def incr(self, key: str, ttl: Optional[int] = None) -> int:
        # Redis: INCR then EXPIRE (only on first bump). In-memory: handles in one call.
        if self.backend_name == "redis":
            value = await self._backend.incr(key)
            if value == 1 and ttl:
                await self._backend.expire(key, ttl)
            return value
        return await self._backend.incr(key, ex=ttl)

    async def ttl(self, key: str) -> int:
        return await self._backend.ttl(key)

    async def ping(self) -> bool:
        try:
            res = await self._backend.ping()
            return bool(res)
        except Exception:  # noqa: BLE001
            return False


# Singleton — imported as ``cache`` across the codebase.
cache = Cache()
