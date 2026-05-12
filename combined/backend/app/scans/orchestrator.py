"""Scan orchestration engine — the heart of TrustScan.

Pipeline stages (executed mostly in parallel):
    1. VALIDATE     — sanitize + SSRF-check target
    2. NORMALIZE    — classify target_type and canonicalise
    3. DISPATCH     — launch URL / DNS / WHOIS / reputation / phishing tasks
    4. AGGREGATE    — merge outputs into a single intelligence blob
    5. SCORE        — run the scoring engine to compute trust/fraud/threat
    6. AI           — generate narrative report (cached)
    7. PERSIST      — write scan row + structured result + indicators + report
    8. CACHE        — memoise the final payload by normalised target
    9. BROADCAST    — stream progress updates to the websocket channel

Every stage publishes a ``scan_progress`` event to channel
``scan:{scan_id}`` so the frontend gets true realtime feedback.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.orchestrator import generate_report as generate_ai_report
from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.core.exceptions import InvalidTargetError, ScanFailedError
from app.dns.resolver import resolve_all
from app.models.scan import AIReport, Scan, ScanResult
from app.models.threat_indicator import ThreatIndicator
from app.phishing.detector import score_phishing
from app.reputation.aggregator import (
    fetch_domain_reputation,
    fetch_email_reputation,
    fetch_ip_reputation,
    fetch_url_reputation,
)
from app.scans.domain_analyzer import analyze_domain
from app.scans.ip_analyzer import analyze_ip
from app.scans.scorer import score as score_payload
from app.scans.url_analyzer import analyze_url
from app.security.sanitizer import detect_target_type, sanitize_url
from app.security.ssrf import validate_ip_target
from app.telemetry.logger import get_logger
from app.utils.time import utcnow
from app.utils.urltools import extract_domain, normalize_url
from app.websocket.manager import manager as ws_manager

log = get_logger(__name__)


# ---------------------------------------------------------------------- helpers
async def _emit(scan_id: str, stage: str, status: str, data: dict | None = None) -> None:
    """Publish a progress event to the scan's websocket channel."""
    await ws_manager.publish(
        f"scan:{scan_id}",
        "scan_progress",
        {"scan_id": scan_id, "stage": stage, "status": status, "data": data or {}},
    )


async def _cache_lookup(normalized: str) -> dict | None:
    return await cache.get_json(ns.scan(normalized))


async def _cache_store(normalized: str, payload: dict) -> None:
    await cache.set_json(ns.scan(normalized), payload, ttl=settings.CACHE_SCAN_TTL)


def _normalise_target(raw: str) -> tuple[str, str]:
    """Return (normalized_target, target_type)."""
    tt = detect_target_type(raw)
    if tt == "url":
        return normalize_url(sanitize_url(raw)), "url"
    if tt == "ip":
        return validate_ip_target(raw.strip()), "ip"
    if tt == "email":
        addr = raw.strip().lower()
        if "@" not in addr:
            raise InvalidTargetError("Invalid email address.")
        return addr, "email"
    # domain
    return extract_domain(raw.strip()), "domain"


# ---------------------------------------------------------------------- pipeline
async def run_pipeline(
    *,
    scan: Scan,
    db: AsyncSession,
) -> dict[str, Any]:
    """Execute the full async pipeline for a scan row.

    The caller owns the ``scan`` row; this function updates it in place.
    Always commits progress snapshots via the provided session.
    """
    started = time.perf_counter()
    scan_id = scan.id
    target = scan.normalized_target
    tt = scan.target_type

    scan.status = "running"
    scan.started_at = utcnow()
    await db.commit()

    await _emit(scan_id, "validate", "done", {"target": target, "target_type": tt})

    # -- cache short-circuit
    cached = await _cache_lookup(target)
    if cached:
        await _emit(scan_id, "complete", "cached", {"trust_score": cached.get("scoring", {}).get("trust_score")})
        return cached

    # ----------------------- stage: DISPATCH (parallel analyzers)
    await _emit(scan_id, "dispatch", "running")

    async def _run_url():
        try:
            return await analyze_url(target)
        except Exception as exc:  # noqa: BLE001
            log.warning("url_analyze_failed", extra={"err": str(exc)[:200]})
            return {"error": str(exc)[:200]}

    async def _run_domain():
        try:
            return await analyze_domain(target)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:200]}

    async def _run_reputation():
        try:
            if tt == "ip":
                return await fetch_ip_reputation(target)
            if tt == "domain":
                return await fetch_domain_reputation(target)
            if tt == "email":
                return await fetch_email_reputation(target)
            return await fetch_url_reputation(target)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:200]}

    async def _run_phishing():
        try:
            return score_phishing(target if tt == "url" else f"https://{target}")
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:200], "score": 0, "indicators": []}

    async def _run_ip():
        if tt != "ip":
            return None
        try:
            return await analyze_ip(target)
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)[:200]}

    url_task = asyncio.create_task(_run_url()) if tt in {"url", "domain"} else None
    domain_task = asyncio.create_task(_run_domain()) if tt in {"url", "domain", "email"} else None
    rep_task = asyncio.create_task(_run_reputation())
    phish_task = asyncio.create_task(_run_phishing()) if tt in {"url", "domain"} else None
    ip_task = asyncio.create_task(_run_ip()) if tt == "ip" else None
    email_domain_task = None
    if tt == "email":
        email_domain = target.split("@", 1)[1]
        email_domain_task = asyncio.create_task(resolve_all(email_domain))

    results_pending = [t for t in (url_task, domain_task, rep_task, phish_task, ip_task, email_domain_task) if t]
    results = await asyncio.gather(*results_pending, return_exceptions=True)
    results = [r if not isinstance(r, Exception) else {"error": str(r)[:200]} for r in results]

    idx = 0
    url_res = results[idx] if url_task else None
    if url_task:
        idx += 1
    domain_res = results[idx] if domain_task else None
    if domain_task:
        idx += 1
    rep_res = results[idx] if rep_task else None
    if rep_task:
        idx += 1
    phish_res = results[idx] if phish_task else None
    if phish_task:
        idx += 1
    ip_res = results[idx] if ip_task else None
    if ip_task:
        idx += 1
    email_dns = results[idx] if email_domain_task else None

    await _emit(scan_id, "dispatch", "done")

    # ----------------------- stage: AGGREGATE
    await _emit(scan_id, "aggregate", "running")
    payload: dict[str, Any] = {
        "target": target,
        "target_type": tt,
        "url": url_res,
        "domain": domain_res,
        "reputation": rep_res,
        "phishing": phish_res,
        "ip": ip_res,
        "email_dns": email_dns,
    }
    # remove None keys for clean output
    payload = {k: v for k, v in payload.items() if v is not None}
    await _emit(scan_id, "aggregate", "done")

    # ----------------------- stage: SCORE
    await _emit(scan_id, "score", "running")
    scoring = score_payload(payload)
    payload["scoring"] = scoring
    await _emit(scan_id, "score", "done", {
        "trust_score": scoring["trust_score"],
        "threat_level": scoring["threat_level"],
        "verdict": scoring["verdict"],
    })

    # ----------------------- stage: AI
    await _emit(scan_id, "ai", "running")
    ai_resp = await generate_ai_report(scan_id, payload)
    payload["ai"] = {
        "provider": ai_resp.provider,
        "model": ai_resp.model,
        "summary": ai_resp.summary,
        "exec_summary": ai_resp.exec_summary,
        "risk_description": ai_resp.risk_description,
        "remediation": ai_resp.remediation,
        "error": ai_resp.error,
    }
    await _emit(scan_id, "ai", "done", {"provider": ai_resp.provider})

    # ----------------------- stage: PERSIST
    duration_ms = int((time.perf_counter() - started) * 1000)
    scan.status = "complete"
    scan.completed_at = utcnow()
    scan.trust_score = scoring["trust_score"]
    scan.fraud_probability = scoring["fraud_probability"]
    scan.threat_level = scoring["threat_level"]
    scan.confidence = scoring["confidence"]
    scan.verdict = scoring["verdict"]

    result_row = ScanResult(scan_id=scan_id, payload=payload, duration_ms=duration_ms)
    db.add(result_row)

    for ind in scoring.get("indicators", []):
        db.add(ThreatIndicator(
            scan_id=scan_id,
            kind=ind.get("kind", "unknown"),
            severity=ind.get("severity", "info"),
            label=ind.get("label", ""),
            description=ind.get("description"),
            score_delta=float(ind.get("score_delta", 0.0)),
        ))

    db.add(AIReport(
        scan_id=scan_id,
        provider=ai_resp.provider,
        model=ai_resp.model,
        summary=ai_resp.summary,
        exec_summary=ai_resp.exec_summary,
        risk_description=ai_resp.risk_description,
        remediation=ai_resp.remediation,
        tokens_in=ai_resp.tokens_in,
        tokens_out=ai_resp.tokens_out,
    ))
    await db.commit()

    # ----------------------- stage: CACHE
    await _cache_store(target, payload)

    # ----------------------- stage: COMPLETE
    await _emit(scan_id, "complete", "done", {
        "scan_id": scan_id,
        "trust_score": scoring["trust_score"],
        "verdict": scoring["verdict"],
        "duration_ms": duration_ms,
    })
    return payload


async def run_scan(*, target_raw: str, db: AsyncSession, user_id: str | None = None) -> Scan:
    """Public entry point — validates the target, creates a scan, executes it."""
    try:
        normalized, tt = _normalise_target(target_raw)
    except InvalidTargetError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InvalidTargetError(str(exc)[:160])

    scan = Scan(
        user_id=user_id,
        target=target_raw,
        target_type=tt,
        normalized_target=normalized,
        status="queued",
    )
    db.add(scan)
    await db.commit()
    await db.refresh(scan)

    try:
        await run_pipeline(scan=scan, db=db)
    except Exception as exc:  # noqa: BLE001
        scan.status = "failed"
        scan.error = str(exc)[:512]
        await db.commit()
        log.exception("scan_failed", extra={"scan_id": scan.id, "target": normalized})
        raise ScanFailedError(message="Scan failed to complete.") from exc

    return scan
