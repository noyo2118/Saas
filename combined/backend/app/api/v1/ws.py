"""/api/v1/ws — websocket channels for live updates."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.telemetry.logger import get_logger
from app.websocket.manager import manager

log = get_logger(__name__)
router = APIRouter(prefix="/ws", tags=["ws"])


@router.websocket("/scans/{scan_id}")
async def ws_scan_progress(ws: WebSocket, scan_id: str):
    """Client subscribes to a specific scan's progress stream."""
    channel = f"scan:{scan_id}"
    await manager.connect(channel, ws)
    try:
        while True:
            # keep the connection alive — drain any incoming pings
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(channel, ws)
    except Exception:  # noqa: BLE001
        await manager.disconnect(channel, ws)


@router.websocket("/threats")
async def ws_threat_feed(ws: WebSocket):
    """Global threat feed broadcast channel."""
    channel = "feed:threats"
    await manager.connect(channel, ws)
    try:
        while True:
            await asyncio.sleep(30)
            await ws.send_json({"event": "heartbeat", "payload": {"ok": True}})
    except WebSocketDisconnect:
        await manager.disconnect(channel, ws)
    except Exception:  # noqa: BLE001
        await manager.disconnect(channel, ws)
