"""/api/v1/intelligence, /api/v1/url, /api/v1/ip, /api/v1/domain, /api/v1/reputation.

Direct, unaggregated intelligence lookups — useful for dashboards and
quick checks without creating a full scan record.
"""
from __future__ import annotations

from fastapi import APIRouter, Query

from app.core.exceptions import InvalidTargetError
from app.dns.resolver import resolve_all
from app.intelligence.registry import all_providers_meta
from app.phishing.detector import score_phishing
from app.reputation.aggregator import (
    fetch_domain_reputation,
    fetch_ip_reputation,
    fetch_url_reputation,
)
from app.scans.domain_analyzer import analyze_domain
from app.scans.ip_analyzer import analyze_ip
from app.scans.url_analyzer import analyze_url
from app.security.sanitizer import sanitize_url
from app.security.ssrf import validate_ip_target
from app.utils.urltools import extract_domain

url_router = APIRouter(prefix="/url", tags=["url"])
ip_router = APIRouter(prefix="/ip", tags=["ip"])
domain_router = APIRouter(prefix="/domain", tags=["domain"])
reputation_router = APIRouter(prefix="/reputation", tags=["reputation"])
intelligence_router = APIRouter(prefix="/intelligence", tags=["intelligence"])


# ---------------------------------------------------------------------- /url
@url_router.get("/analyze")
async def url_analyze(target: str = Query(..., min_length=1)) -> dict:
    url = sanitize_url(target)
    return {
        "ok": True,
        "data": {
            "url_analysis": await analyze_url(url),
            "phishing": score_phishing(url),
        },
    }


# ---------------------------------------------------------------------- /ip
@ip_router.get("/analyze")
async def ip_analyze(target: str = Query(..., min_length=1)) -> dict:
    ip = validate_ip_target(target.strip())
    return {"ok": True, "data": await analyze_ip(ip)}


# ---------------------------------------------------------------------- /domain
@domain_router.get("/analyze")
async def domain_analyze(target: str = Query(..., min_length=1)) -> dict:
    domain = extract_domain(target)
    if not domain or "." not in domain:
        raise InvalidTargetError("Invalid domain.")
    return {"ok": True, "data": await analyze_domain(domain)}


@domain_router.get("/dns")
async def domain_dns(target: str = Query(..., min_length=1)) -> dict:
    domain = extract_domain(target)
    return {"ok": True, "data": await resolve_all(domain)}


# ---------------------------------------------------------------------- /reputation
@reputation_router.get("/url")
async def rep_url(target: str = Query(..., min_length=1)) -> dict:
    url = sanitize_url(target)
    return {"ok": True, "data": await fetch_url_reputation(url)}


@reputation_router.get("/ip")
async def rep_ip(target: str = Query(..., min_length=1)) -> dict:
    ip = validate_ip_target(target.strip())
    return {"ok": True, "data": await fetch_ip_reputation(ip)}


@reputation_router.get("/domain")
async def rep_domain(target: str = Query(..., min_length=1)) -> dict:
    domain = extract_domain(target)
    return {"ok": True, "data": await fetch_domain_reputation(domain)}


# ---------------------------------------------------------------------- /intelligence
@intelligence_router.get("/providers")
async def providers() -> dict:
    return {"ok": True, "data": all_providers_meta()}
