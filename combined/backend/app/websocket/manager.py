"""Websocket connection manager + in-process pub/sub.

Each logical ``channel`` is a set of connections. Messages published to a
channel are fanned out to every connected client on that instance.

For multi-instance deployments, swap ``_local_bus`` for a Redis pub/sub
bridge without touching callers — the interface is the same.
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

from app.telemetry.logger import get_logger

log = get_logger(__name__)


class WebSocketManager:
    def __init__(self) -> None:
        self._channels: dict[str, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    # -------------------------------------------------- connection lifecycle
    async def connect(self, channel: str, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._channels[channel].add(ws)
        log.info("ws_connected", extra={"channel": channel, "peers": len(self._channels[channel])})

    async def disconnect(self, channel: str, ws: WebSocket) -> None:
        async with self._lock:
            self._channels[channel].discard(ws)
            if not self._channels[channel]:
                self._channels.pop(channel, None)
        log.info("ws_disconnected", extra={"channel": channel})

    # -------------------------------------------------- broadcasting
    async def publish(self, channel: str, event: str, payload: Any) -> None:
        """Send an event to every subscriber on the channel."""
        async with self._lock:
            targets = list(self._channels.get(channel, ()))
        message = {"event": event, "payload": payload}
        if not targets:
            return
        await asyncio.gather(
            *(self._safe_send(ws, message) for ws in targets),
            return_exceptions=True,
        )

    async def broadcast_all(self, event: str, payload: Any) -> None:
        async with self._lock:
            targets = [ws for conns in self._channels.values() for ws in conns]
        await asyncio.gather(
            *(self._safe_send(ws, {"event": event, "payload": payload}) for ws in targets),
            return_exceptions=True,
        )

    async def _safe_send(self, ws: WebSocket, message: dict) -> None:
        try:
            await ws.send_json(message)
        except Exception as exc:  # noqa: BLE001
            log.debug("ws_send_failed", extra={"err": str(exc)})


manager = WebSocketManager()
