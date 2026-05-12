"""Prompt engineering + response parsing shared across AI providers."""
from __future__ import annotations

import re
from typing import Any

_TEMPLATE = """You are a senior cybersecurity analyst writing for both a non-technical user and an executive.
Produce STRICT JSON with exactly these keys (no prose, no markdown fences):
{{
  "summary": "2-3 plain-English sentences for a non-technical user",
  "exec_summary": "1-2 sentence executive summary with risk framing",
  "risk_description": "Specific risks grounded in the scan signals below",
  "remediation": "Concrete next steps the user should take"
}}

Ground every statement in these REAL scan signals. Do not invent data.

TARGET: {target}
TYPE: {target_type}
TRUST SCORE: {trust_score}/100
VERDICT: {verdict}
FRAUD PROBABILITY: {fraud}
THREAT LEVEL: {threat_level}
HTTPS: {https}
SSL valid: {ssl_valid}
Domain age (days): {age_days}
Reputation malicious: {rep_mal}
Reputation categories: {rep_cats}
Phishing heuristic score: {phish_score}
Key indicators: {top_indicators}
"""


def build_prompt(ctx: dict[str, Any]) -> str:
    top = ctx.get("indicators") or []
    top = [i.get("label") for i in top[:8] if isinstance(i, dict)]
    return _TEMPLATE.format(
        target=ctx.get("target", ""),
        target_type=ctx.get("target_type", ""),
        trust_score=ctx.get("trust_score", "n/a"),
        verdict=ctx.get("verdict", "n/a"),
        fraud=ctx.get("fraud_probability", "n/a"),
        threat_level=ctx.get("threat_level", "n/a"),
        https=ctx.get("https", "n/a"),
        ssl_valid=ctx.get("ssl_valid", "n/a"),
        age_days=ctx.get("age_days", "unknown"),
        rep_mal=ctx.get("rep_malicious", "n/a"),
        rep_cats=", ".join(ctx.get("rep_categories") or []) or "none",
        phish_score=ctx.get("phishing_score", "n/a"),
        top_indicators="; ".join(top) or "none",
    )


_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def parse_response(text: str) -> dict[str, str | None]:
    """Extract the JSON block — tolerant of surrounding text / code fences."""
    if not text:
        return {}
    match = _JSON_BLOCK.search(text)
    if not match:
        return {"summary": text.strip()[:800]}
    raw = match.group(0)
    try:
        import orjson

        obj = orjson.loads(raw)
    except Exception:  # noqa: BLE001
        try:
            import json

            obj = json.loads(raw)
        except Exception:  # noqa: BLE001
            return {"summary": text.strip()[:800]}
    return {
        "summary": obj.get("summary"),
        "exec_summary": obj.get("exec_summary"),
        "risk_description": obj.get("risk_description"),
        "remediation": obj.get("remediation"),
    }


def fallback_report(ctx: dict[str, Any]) -> dict[str, str]:
    """Deterministic report when no AI provider is configured."""
    verdict = ctx.get("verdict", "Unknown")
    trust = ctx.get("trust_score", 0)
    top = ctx.get("indicators") or []
    top_labels = [i.get("label") for i in top[:4] if isinstance(i, dict)]

    if verdict == "Trusted":
        summary = (
            f"{ctx.get('target','This target')} scored {trust}/100 and appears trusted. "
            "Valid TLS, established domain, and no reputation flags."
        )
        remediation = "Proceed normally but always verify the exact URL before entering credentials."
    elif verdict == "Suspicious":
        summary = (
            f"{ctx.get('target','This target')} scored {trust}/100 and shows mixed signals. "
            "Treat with caution until verified."
        )
        remediation = "Avoid entering passwords or payment info until you independently confirm the site."
    elif verdict == "High risk":
        summary = (
            f"{ctx.get('target','This target')} scored {trust}/100 — multiple high-risk signals detected."
        )
        remediation = "Do not interact with this site. Report to your security team."
    else:
        summary = (
            f"{ctx.get('target','This target')} is critical: trust {trust}/100, active threat signals."
        )
        remediation = "Block the domain/IP and investigate any systems that contacted it."

    return {
        "summary": summary,
        "exec_summary": f"Verdict: {verdict} (trust {trust}/100).",
        "risk_description": "Top signals: " + "; ".join(top_labels) if top_labels else "No major signals.",
        "remediation": remediation,
    }
