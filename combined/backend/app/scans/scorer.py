"""Unified Threat Scoring Engine.

Modular, weight-based scoring that consumes the outputs of every analyzer
(URL, SSL, DNS, WHOIS, phishing heuristics, reputation aggregator) and
produces the final trust / fraud / threat numbers.

Every scoring rule lives in a single RULES table — add/remove weights by
editing the list, no branching logic required.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(slots=True)
class Rule:
    kind: str
    label: str
    severity: str  # info|low|medium|high|critical
    weight: float  # positive = good (adds), negative = bad (subtracts)
    predicate: Callable[[dict], bool]
    description: str = ""


def _g(d: dict, *path, default=None):
    cur: Any = d
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


RULES: list[Rule] = [
    # ---------- transport / TLS (up to 30)
    Rule("https", "HTTPS enabled", "info", 10,
         lambda r: bool(_g(r, "url", "https"))),
    Rule("ssl_valid", "SSL certificate valid", "info", 12,
         lambda r: bool(_g(r, "url", "ssl", "valid"))),
    Rule("ssl_expired", "SSL certificate expired", "high", -15,
         lambda r: bool(_g(r, "url", "ssl", "expired"))),
    Rule("ssl_expiring_soon", "SSL expires within 30 days", "medium", -4,
         lambda r: bool(_g(r, "url", "ssl", "expiring_soon"))),

    # ---------- security headers (up to 15)
    Rule("csp_header", "Content-Security-Policy present", "info", 4,
         lambda r: bool(_g(r, "url", "header_flags", "csp"))),
    Rule("xframe_header", "X-Frame-Options present", "info", 3,
         lambda r: bool(_g(r, "url", "header_flags", "xframe"))),
    Rule("hsts_header", "HSTS present", "info", 3,
         lambda r: bool(_g(r, "url", "header_flags", "hsts"))),
    Rule("xcontent_header", "X-Content-Type-Options present", "info", 2,
         lambda r: bool(_g(r, "url", "header_flags", "xcontent"))),
    Rule("referrer_header", "Referrer-Policy present", "info", 1.5,
         lambda r: bool(_g(r, "url", "header_flags", "referrer"))),
    Rule("permissions_header", "Permissions-Policy present", "info", 1.5,
         lambda r: bool(_g(r, "url", "header_flags", "permissions"))),

    # ---------- redirects
    Rule("redirects_reasonable", "Redirects <= 3", "info", 3,
         lambda r: (_g(r, "url", "redirects", default=0) or 0) <= 3),
    Rule("redirects_excessive", "Excessive redirects (>3)", "medium", -6,
         lambda r: (_g(r, "url", "redirects", default=0) or 0) > 3),
    Rule("cross_host_redirect", "Redirect crosses hosts", "low", -3,
         lambda r: bool(_g(r, "url", "cross_host_redirect"))),

    # ---------- domain age / WHOIS
    Rule("domain_age_5y", "Domain older than 5 years", "info", 15,
         lambda r: (_g(r, "domain", "whois", "age_days") or 0) > 5 * 365),
    Rule("domain_age_1y", "Domain older than 1 year", "info", 10,
         lambda r: 365 < (_g(r, "domain", "whois", "age_days") or 0) <= 5 * 365),
    Rule("domain_age_6m", "Domain 6-12 months old", "low", 3,
         lambda r: 180 < (_g(r, "domain", "whois", "age_days") or 0) <= 365),
    Rule("domain_brand_new", "Domain < 30 days old", "high", -15,
         lambda r: 0 <= (_g(r, "domain", "whois", "age_days") or -1) < 30),
    Rule("domain_new", "Domain 30-180 days old", "medium", -8,
         lambda r: 30 <= (_g(r, "domain", "whois", "age_days") or -1) < 180),
    Rule("whois_private", "WHOIS data unavailable", "low", -2,
         lambda r: _g(r, "domain", "whois", "age_days") is None),

    # ---------- reputation (up to 20)
    Rule("rep_clean", "Not flagged by reputation feeds", "info", 15,
         lambda r: _g(r, "reputation", "malicious") is False
                   and (_g(r, "reputation", "confidence", default=0) or 0) >= 0.4),
    Rule("rep_malicious", "Flagged malicious by reputation feeds", "critical", -40,
         lambda r: _g(r, "reputation", "malicious") is True),

    # ---------- phishing heuristics
    Rule("phish_low", "Phishing heuristic score low", "info", 5,
         lambda r: (_g(r, "phishing", "score") or 0) < 15),
    Rule("phish_medium", "Phishing heuristic moderate", "medium", -8,
         lambda r: 15 <= (_g(r, "phishing", "score") or 0) < 40),
    Rule("phish_high", "Phishing heuristic high", "high", -20,
         lambda r: 40 <= (_g(r, "phishing", "score") or 0) < 70),
    Rule("phish_critical", "Phishing heuristic critical", "critical", -30,
         lambda r: (_g(r, "phishing", "score") or 0) >= 70),

    # ---------- suspicious body patterns
    Rule("body_password_field", "Password field present on scanned page", "low", -1,
         lambda r: "password_field" in (_g(r, "url", "body_patterns") or [])),
    Rule("body_eval", "JavaScript eval() detected", "medium", -3,
         lambda r: "eval_call" in (_g(r, "url", "body_patterns") or [])),
    Rule("body_iframe_external", "External iframe detected", "low", -2,
         lambda r: "iframe_external" in (_g(r, "url", "body_patterns") or [])),

    # ---------- TLD / infrastructure
    Rule("suspicious_tld", "Suspicious TLD", "medium", -5,
         lambda r: bool(_g(r, "domain", "suspicious_tld"))),

    # ---------- email config (domain scans)
    Rule("email_config", "SPF + MX configured", "info", 2,
         lambda r: bool(_g(r, "domain", "dns", "has_email_config"))),
]


def _level(score: float) -> tuple[str, str]:
    if score >= 85:
        return "low", "Trusted"
    if score >= 65:
        return "moderate", "Suspicious"
    if score >= 40:
        return "high", "High risk"
    return "critical", "Critical"


def score(payload: dict) -> dict[str, Any]:
    """Run every rule against the payload and return trust/fraud/threat."""
    base = 50.0
    total = base
    indicators: list[dict] = []

    for rule in RULES:
        try:
            matched = rule.predicate(payload)
        except Exception:  # noqa: BLE001
            matched = False
        if matched:
            total += rule.weight
            indicators.append({
                "kind": rule.kind,
                "label": rule.label,
                "severity": rule.severity,
                "score_delta": rule.weight,
                "description": rule.description,
            })

    trust_score = max(0.0, min(100.0, round(total, 1)))
    fraud_probability = round(1.0 - (trust_score / 100.0), 3)
    threat_level, verdict = _level(trust_score)

    # confidence = reputation confidence + "how many rules fired"
    rep_conf = float(_g(payload, "reputation", "confidence") or 0)
    fired_ratio = min(1.0, len(indicators) / 10.0)
    confidence = round(min(1.0, 0.4 * fired_ratio + 0.6 * rep_conf + 0.1), 3)

    return {
        "trust_score": trust_score,
        "fraud_probability": fraud_probability,
        "threat_level": threat_level,
        "verdict": verdict,
        "confidence": confidence,
        "indicators": indicators,
    }
