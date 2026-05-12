"""/api/v1/admin — admin-only endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field, IPvAnyAddress
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_admin
from app.database.session import get_db
from app.intelligence.registry import all_providers_meta
from app.models.scan import Scan
from app.models.user import User
from app.monitoring.metrics import metrics
from app.schemas.common import MessageResponse
from app.security import ipban

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/stats")
async def stats(db: AsyncSession = Depends(get_db)) -> dict:
    users = await db.scalar(select(func.count()).select_from(User))
    scans = await db.scalar(select(func.count()).select_from(Scan))
    malicious = await db.scalar(
        select(func.count()).select_from(Scan).where(Scan.threat_level.in_(["high", "critical"]))
    )
    return {
        "ok": True,
        "data": {
            "users": users or 0,
            "scans": scans or 0,
            "high_risk_scans": malicious or 0,
            "providers": all_providers_meta(),
        },
    }


@router.get("/metrics")
async def get_metrics() -> dict:
    return {"ok": True, "data": await metrics.snapshot()}


# ---------------------------------------------------------------------- ipban
class BanIn(BaseModel):
    ip: IPvAnyAddress
    reason: str = Field(default="manual", max_length=120)
    ttl_seconds: int | None = Field(default=None, ge=60, le=60 * 60 * 24 * 30)


class UnbanIn(BaseModel):
    ip: IPvAnyAddress


@router.post("/ipban", response_model=MessageResponse)
async def ban_ip(body: BanIn) -> MessageResponse:
    ok = await ipban.ban(str(body.ip), reason=body.reason, ttl=body.ttl_seconds)
    if not ok:
        return MessageResponse(ok=False, message="Invalid IP.")
    return MessageResponse(ok=True, message=f"Banned {body.ip}.")


@router.post("/ipban/remove", response_model=MessageResponse)
async def unban_ip(body: UnbanIn) -> MessageResponse:
    await ipban.unban(str(body.ip))
    return MessageResponse(ok=True, message=f"Unbanned {body.ip}.")


@router.get("/ipban/{ip}")
async def ipban_status(ip: str) -> dict:
    banned = await ipban.is_banned(ip)
    return {
        "ok": True,
        "data": {
            "ip": ip,
            "banned": banned,
            "reason": await ipban.reason_for(ip) if banned else None,
        },
    }
