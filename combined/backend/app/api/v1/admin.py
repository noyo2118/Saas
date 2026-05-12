"""/api/v1/admin — admin-only endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import require_admin
from app.database.session import get_db
from app.intelligence.registry import all_providers_meta
from app.models.scan import Scan
from app.models.user import User
from app.monitoring.metrics import metrics

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
