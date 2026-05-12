"""Domain intelligence — WHOIS, DNS, registrar reputation, age."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.dns.resolver import resolve_all
from app.telemetry.logger import get_logger
from app.utils.urltools import extract_domain, is_suspicious_tld, tld_of

log = get_logger(__name__)


def _to_naive(dt):
    if dt is None or not isinstance(dt, datetime):
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _sync_whois(domain: str) -> dict[str, Any]:
    try:
        import whois  # python-whois

        d = whois.whois(domain)

        def pick(v):
            return v[0] if isinstance(v, list) and v else v

        created = _to_naive(pick(d.creation_date))
        expires = _to_naive(pick(d.expiration_date))
        updated = _to_naive(pick(d.updated_date))
        registrar = pick(d.registrar)

        ns_list = d.name_servers
        if isinstance(ns_list, list):
            ns_list = list(dict.fromkeys((s or "").lower().rstrip(".") for s in ns_list))[:6]
        elif isinstance(ns_list, str):
            ns_list = [ns_list.lower().rstrip(".")]
        else:
            ns_list = []

        if created is None:
            return {
                "domain": domain,
                "available": False,
                "age_days": None,
                "age_years": None,
                "creation_date": None,
                "expiry_date": None,
                "updated_date": None,
                "days_to_expiry": None,
                "registrar": registrar,
                "name_servers": ns_list,
                "is_new": None,
                "error": "whois_no_creation_date",
            }

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        age_days = (now - created).days
        days_to_expiry = (expires - now).days if expires else None

        return {
            "domain": domain,
            "available": True,
            "age_days": age_days,
            "age_years": round(age_days / 365.0, 2),
            "creation_date": created.date().isoformat(),
            "expiry_date": expires.date().isoformat() if expires else None,
            "updated_date": updated.date().isoformat() if updated else None,
            "days_to_expiry": days_to_expiry,
            "registrar": registrar,
            "name_servers": ns_list,
            "is_new": age_days < 180,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "domain": domain,
            "available": False,
            "age_days": None,
            "age_years": None,
            "creation_date": None,
            "expiry_date": None,
            "updated_date": None,
            "days_to_expiry": None,
            "registrar": None,
            "name_servers": [],
            "is_new": None,
            "error": str(exc)[:160],
        }


async def _whois_cached(domain: str) -> dict[str, Any]:
    key = ns.whois(domain)
    cached = await cache.get_json(key)
    if cached is not None:
        return cached
    result = await asyncio.to_thread(_sync_whois, domain)
    # cache longer when we got data, shorter when we failed
    ttl = 86400 if result.get("available") else 600
    await cache.set_json(key, result, ttl=ttl)
    return result


async def analyze_domain(target: str) -> dict[str, Any]:
    """Runs WHOIS + DNS in parallel and produces a merged intelligence blob."""
    domain = extract_domain(target)
    whois_task = _whois_cached(domain)
    dns_task = resolve_all(domain)
    whois_info, dns_info = await asyncio.gather(whois_task, dns_task)

    tld = tld_of(domain)
    return {
        "domain": domain,
        "tld": tld,
        "suspicious_tld": is_suspicious_tld(domain),
        "whois": whois_info,
        "dns": dns_info,
    }
