"""/api/v1/scans — orchestrated scan endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth.deps import get_optional_user
from app.core.exceptions import NotFoundError
from app.database.session import get_db
from app.models.scan import Scan, ScanResult
from app.models.user import User
from app.scans.orchestrator import run_scan
from app.schemas.common import MessageResponse
from app.schemas.scans import AIReportOut, IndicatorOut, ScanDetail, ScanRequest, ScanSummary

router = APIRouter(prefix="/scans", tags=["scans"])


def _to_summary(s: Scan) -> ScanSummary:
    return ScanSummary(
        id=s.id,
        target=s.target,
        target_type=s.target_type,
        normalized_target=s.normalized_target,
        status=s.status,
        trust_score=s.trust_score,
        fraud_probability=s.fraud_probability,
        threat_level=s.threat_level,
        verdict=s.verdict,
        confidence=s.confidence,
        created_at=s.created_at,
        completed_at=s.completed_at,
    )


@router.post("", response_model=ScanDetail)
async def create_scan(
    body: ScanRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> ScanDetail:
    """Run a new scan (synchronous — streams progress over /ws/scans/{id})."""
    scan = await run_scan(
        target_raw=body.target,
        db=db,
        user_id=user.id if user else None,
    )
    return await _detail(db, scan.id)


@router.get("", response_model=list[ScanSummary])
async def list_scans(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> list[ScanSummary]:
    stmt = select(Scan).order_by(desc(Scan.created_at)).limit(limit)
    if user:
        stmt = stmt.where(Scan.user_id == user.id)
    res = await db.execute(stmt)
    return [_to_summary(s) for s in res.scalars().all()]


@router.get("/{scan_id}", response_model=ScanDetail)
async def get_scan(scan_id: str, db: AsyncSession = Depends(get_db)) -> ScanDetail:
    return await _detail(db, scan_id)


async def _detail(db: AsyncSession, scan_id: str) -> ScanDetail:
    stmt = (
        select(Scan)
        .where(Scan.id == scan_id)
        .options(
            selectinload(Scan.result),
            selectinload(Scan.ai_report),
            selectinload(Scan.indicators),
        )
    )
    res = await db.execute(stmt)
    scan: Scan | None = res.scalars().first()
    if not scan:
        raise NotFoundError("Scan not found.")

    payload = scan.result.payload if scan.result else {}
    indicators = [
        IndicatorOut(
            kind=i.kind, label=i.label, severity=i.severity,
            score_delta=i.score_delta, description=i.description,
        )
        for i in scan.indicators
    ]
    ai = None
    if scan.ai_report:
        ai = AIReportOut(
            provider=scan.ai_report.provider,
            model=scan.ai_report.model,
            summary=scan.ai_report.summary,
            exec_summary=scan.ai_report.exec_summary,
            risk_description=scan.ai_report.risk_description,
            remediation=scan.ai_report.remediation,
        )

    return ScanDetail(
        **_to_summary(scan).model_dump(),
        payload=payload,
        indicators=indicators,
        ai_report=ai,
    )


@router.delete("/{scan_id}", response_model=MessageResponse)
async def delete_scan(scan_id: str, db: AsyncSession = Depends(get_db)) -> MessageResponse:
    res = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = res.scalars().first()
    if not scan:
        raise NotFoundError("Scan not found.")
    await db.delete(scan)
    await db.commit()
    return MessageResponse(ok=True, message="Scan deleted.")
