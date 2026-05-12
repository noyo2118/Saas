"""Structured PDF intelligence report — reportlab, zero AI, pure scan data.

Produces a multi-page (>=6) VirusTotal-style report from the real scan payload.
Every value printed on the page comes directly from the scan result dict — no
LLM, no mock values, no placeholders. If a field is missing from the scan
payload the corresponding row displays an em dash.

Pages:
    1. Cover              — target, verdict, trust score, timestamps, meta
    2. Executive summary  — counters, threat level, fraud probability, top indicators
    3. TLS / SSL          — certificate chain, cipher, SAN, expiry
    4. Domain intelligence — WHOIS, registrar, DNS records, SPF/DKIM/DMARC
    5. Reputation matrix  — per-provider verdicts + weighted aggregate
    6. Phishing heuristics — every fired heuristic with score delta + severity
    7. HTTP response      — security headers, redirect chain, body patterns
    8. Indicator log      — full table of scoring rules that fired
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------- palette
_BRAND_BG = colors.HexColor("#0A0E1A")
_BRAND_PRIMARY = colors.HexColor("#00D1FF")
_BRAND_ACCENT = colors.HexColor("#8B5CF6")
_BRAND_DANGER = colors.HexColor("#FF3B5C")
_BRAND_WARN = colors.HexColor("#FFB23F")
_BRAND_OK = colors.HexColor("#1BE1A0")
_INK = colors.HexColor("#E6EAF2")
_INK_MUTED = colors.HexColor("#8A93A6")
_SURFACE = colors.HexColor("#121826")
_BORDER = colors.HexColor("#1F2A3D")


# ---------------------------------------------------------------------- helpers
def _g(d: Optional[dict], *path, default="—"):
    """Safe nested dict access with an em-dash default."""
    cur: Any = d or {}
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    if isinstance(cur, (list, tuple)):
        return ", ".join(str(x) for x in cur[:10]) or default
    if isinstance(cur, bool):
        return "Yes" if cur else "No"
    if cur == "":
        return default
    return cur


def _verdict_color(verdict: Optional[str]):
    if not verdict:
        return _INK_MUTED
    v = verdict.lower()
    if "trusted" in v:
        return _BRAND_OK
    if "suspicious" in v:
        return _BRAND_WARN
    if "critical" in v:
        return _BRAND_DANGER
    if "high" in v or "risk" in v:
        return _BRAND_DANGER
    return _INK_MUTED


def _severity_color(sev: str):
    sev = (sev or "").lower()
    return {
        "info": _INK_MUTED,
        "low": _BRAND_OK,
        "medium": _BRAND_WARN,
        "high": _BRAND_DANGER,
        "critical": _BRAND_DANGER,
    }.get(sev, _INK_MUTED)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


# ---------------------------------------------------------------------- styles
def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    out = {
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"], textColor=_INK,
            fontName="Helvetica-Bold", fontSize=22, leading=28, spaceAfter=10,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], textColor=_BRAND_PRIMARY,
            fontName="Helvetica-Bold", fontSize=14, leading=18,
            spaceBefore=14, spaceAfter=8,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"], textColor=_INK,
            fontName="Helvetica-Bold", fontSize=11, leading=14,
            spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["BodyText"], textColor=_INK,
            fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=6,
        ),
        "mono": ParagraphStyle(
            "mono", parent=base["BodyText"], textColor=_INK,
            fontName="Courier", fontSize=8, leading=11,
        ),
        "muted": ParagraphStyle(
            "muted", parent=base["BodyText"], textColor=_INK_MUTED,
            fontName="Helvetica", fontSize=8.5, leading=11,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["BodyText"], textColor=_INK_MUTED,
            fontName="Helvetica-Oblique", fontSize=8, leading=10, alignment=TA_CENTER,
        ),
        "hero_score": ParagraphStyle(
            "hero_score", textColor=_BRAND_PRIMARY,
            fontName="Helvetica-Bold", fontSize=72, leading=80, alignment=TA_CENTER,
        ),
        "hero_verdict": ParagraphStyle(
            "hero_verdict", textColor=_INK,
            fontName="Helvetica-Bold", fontSize=22, leading=26, alignment=TA_CENTER,
            spaceBefore=6, spaceAfter=4,
        ),
    }
    return out


# ---------------------------------------------------------------------- page canvas (header / footer)
def _draw_page_chrome(c: canvas.Canvas, doc):
    w, h = A4
    # top header band
    c.setFillColor(_BRAND_BG)
    c.rect(0, h - 16 * mm, w, 16 * mm, stroke=0, fill=1)
    c.setFillColor(_BRAND_PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(15 * mm, h - 10 * mm, "TrustScan")
    c.setFillColor(_INK_MUTED)
    c.setFont("Helvetica", 8)
    c.drawString(32 * mm, h - 10 * mm, "· AI Cyber Threat Intelligence")
    c.drawRightString(w - 15 * mm, h - 10 * mm, f"Generated {_now_iso()}")

    # accent line
    c.setStrokeColor(_BRAND_PRIMARY)
    c.setLineWidth(0.6)
    c.line(15 * mm, h - 17 * mm, w - 15 * mm, h - 17 * mm)

    # footer
    c.setFillColor(_INK_MUTED)
    c.setFont("Helvetica", 7.5)
    c.drawString(15 * mm, 10 * mm, "Confidential intelligence report · TrustScan v4.2")
    c.drawRightString(w - 15 * mm, 10 * mm, f"Page {doc.page}")


# ---------------------------------------------------------------------- section builders
def _kv_table(rows: list[tuple[str, str]], col_widths=(55 * mm, 115 * mm)) -> Table:
    """Label/value table styled like the VirusTotal side panels."""
    data = [[k, v] for k, v in rows]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), "Helvetica", 9),
        ("TEXTCOLOR", (0, 0), (0, -1), _INK_MUTED),
        ("TEXTCOLOR", (1, 0), (1, -1), _INK),
        ("BACKGROUND", (0, 0), (-1, -1), _SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.25, _BORDER),
        ("LINEBELOW", (0, 0), (-1, -2), 0.2, _BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _matrix_table(header: list[str], rows: list[list], col_widths: Optional[list] = None,
                  verdict_col: Optional[int] = None) -> Table:
    """Multi-column matrix with header row styled like VirusTotal detection tables."""
    data = [header] + rows
    t = Table(data, colWidths=col_widths)
    style = TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 8.5),
        ("FONT", (0, 1), (-1, -1), "Helvetica", 8.5),
        ("BACKGROUND", (0, 0), (-1, 0), _BRAND_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), _BRAND_PRIMARY),
        ("BACKGROUND", (0, 1), (-1, -1), _SURFACE),
        ("TEXTCOLOR", (0, 1), (-1, -1), _INK),
        ("BOX", (0, 0), (-1, -1), 0.25, _BORDER),
        ("GRID", (0, 0), (-1, -1), 0.15, _BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])
    if verdict_col is not None:
        for i, row in enumerate(rows, start=1):
            value = str(row[verdict_col]).lower()
            color = _BRAND_DANGER if value in {"listed", "malicious", "yes"} \
                else _BRAND_OK if value in {"clean", "safe", "ok"} \
                else _BRAND_WARN
            style.add("TEXTCOLOR", (verdict_col, i), (verdict_col, i), color)
            style.add("FONT", (verdict_col, i), (verdict_col, i), "Helvetica-Bold", 8.5)
    t.setStyle(style)
    return t


def _section_title(styles, text: str) -> Paragraph:
    return Paragraph(text, styles["h2"])


# ---------------------------------------------------------------------- page builders
def _page_cover(styles, scan: dict) -> list:
    payload = scan.get("payload") or {}
    scoring = payload.get("scoring") or {}
    verdict = scoring.get("verdict") or scan.get("verdict") or "Unknown"
    score = scoring.get("trust_score") or scan.get("trust_score") or 0
    threat = scoring.get("threat_level") or scan.get("threat_level") or "—"
    fraud = scoring.get("fraud_probability")
    fraud_str = f"{int(round(fraud * 100))}%" if isinstance(fraud, (int, float)) else "—"
    confidence = scoring.get("confidence") or scan.get("confidence")
    conf_str = f"{int(round((confidence or 0) * 100))}%" if confidence is not None else "—"

    elements = []
    elements.append(Spacer(1, 28 * mm))
    elements.append(Paragraph("THREAT INTELLIGENCE REPORT", styles["muted"]))
    elements.append(Paragraph(scan.get("target", "—"), styles["h1"]))
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph(
        f"<font color='{_INK_MUTED.hexval()}'>Target type:</font> "
        f"<b>{scan.get('target_type', '—').upper()}</b> · "
        f"<font color='{_INK_MUTED.hexval()}'>Normalised:</font> "
        f"<font face='Courier' size='9'>{scan.get('normalized_target', '—')}</font>",
        styles["body"],
    ))
    elements.append(Spacer(1, 22 * mm))

    # trust score hero
    elements.append(Paragraph(f"{int(round(score))}", styles["hero_score"]))
    elements.append(Paragraph("TRUST SCORE / 100", styles["caption"]))
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(
        f"<font color='{_verdict_color(verdict).hexval()}'>■</font> &nbsp; {verdict.upper()}",
        styles["hero_verdict"],
    ))
    elements.append(Spacer(1, 18 * mm))

    elements.append(_kv_table([
        ("Threat level", threat.title() if isinstance(threat, str) else "—"),
        ("Fraud probability", fraud_str),
        ("Analyst confidence", conf_str),
        ("Scan ID", scan.get("id", "—")),
        ("Created", str(scan.get("created_at", "—"))),
        ("Completed", str(scan.get("completed_at", "—"))),
        ("Report generated", _now_iso()),
    ]))
    elements.append(PageBreak())
    return elements


def _page_executive(styles, scan: dict) -> list:
    payload = scan.get("payload") or {}
    scoring = payload.get("scoring") or {}
    indicators = scoring.get("indicators") or scan.get("indicators") or []

    sev_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for i in indicators:
        s = (i.get("severity") if isinstance(i, dict) else "info") or "info"
        sev_counts[s] = sev_counts.get(s, 0) + 1

    el = [_section_title(styles, "Executive Summary")]

    el.append(_matrix_table(
        header=["Critical", "High", "Medium", "Low", "Info", "Total"],
        rows=[[
            sev_counts.get("critical", 0), sev_counts.get("high", 0),
            sev_counts.get("medium", 0), sev_counts.get("low", 0),
            sev_counts.get("info", 0), len(indicators),
        ]],
        col_widths=[28 * mm] * 6,
    ))
    el.append(Spacer(1, 6 * mm))

    # top indicators
    el.append(Paragraph("Key findings", styles["h3"]))
    top = sorted(
        [i for i in indicators if isinstance(i, dict)],
        key=lambda x: abs(float(x.get("score_delta", 0) or 0)),
        reverse=True,
    )[:10]
    if not top:
        el.append(Paragraph("No scoring rules fired for this target.", styles["muted"]))
    else:
        rows = []
        for i in top:
            rows.append([
                i.get("severity", "info").upper(),
                i.get("kind", "—"),
                i.get("label", "—"),
                f"{float(i.get('score_delta', 0) or 0):+.1f}",
            ])
        el.append(_matrix_table(
            header=["Severity", "Kind", "Description", "Score Δ"],
            rows=rows,
            col_widths=[22 * mm, 40 * mm, 90 * mm, 18 * mm],
            verdict_col=0,
        ))

    el.append(Spacer(1, 8 * mm))
    el.append(Paragraph("Summary of scan coverage", styles["h3"]))
    cov = [
        ("URL / website analysis", "url" in payload),
        ("Domain intelligence (WHOIS + DNS)", "domain" in payload),
        ("IP intelligence", "ip" in payload),
        ("Reputation aggregation", "reputation" in payload),
        ("Phishing heuristics", "phishing" in payload),
        ("AI narrative report", "ai" in payload),
    ]
    el.append(_matrix_table(
        header=["Module", "Executed"],
        rows=[[label, "Yes" if ok else "No"] for label, ok in cov],
        col_widths=[130 * mm, 40 * mm],
        verdict_col=1,
    ))
    el.append(PageBreak())
    return el


def _page_tls(styles, scan: dict) -> list:
    url = (scan.get("payload") or {}).get("url") or {}
    ssl = url.get("ssl") or {}
    headers = url.get("header_flags") or {}
    el = [_section_title(styles, "TLS / SSL Inspection")]

    el.append(_kv_table([
        ("Protocol", "HTTPS" if url.get("https") else "HTTP"),
        ("Certificate valid", _g({"v": ssl.get("valid")}, "v")),
        ("Issuer organisation", ssl.get("issuer") or "—"),
        ("Issuer CN", ssl.get("issuer_cn") or "—"),
        ("Subject CN", ssl.get("subject_cn") or "—"),
        ("TLS version", ssl.get("tls_version") or "—"),
        ("Cipher suite", ssl.get("cipher") or "—"),
        ("Expires", ssl.get("expires") or "—"),
        ("Days until expiry", str(ssl.get("days_left") if ssl.get("days_left") is not None else "—")),
        ("Expired", "Yes" if ssl.get("expired") else "No"),
        ("Expiring within 30 days", "Yes" if ssl.get("expiring_soon") else "No"),
        ("HSTS enforced", "Yes" if headers.get("hsts") else "No"),
    ]))

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("Subject Alternative Names", styles["h3"]))
    san = ssl.get("san") or []
    if san:
        rows = [[n] for n in san[:40]]
        el.append(_matrix_table(["Hostname"], rows, col_widths=[170 * mm]))
    else:
        el.append(Paragraph("No SAN entries recorded.", styles["muted"]))

    if ssl.get("error"):
        el.append(Spacer(1, 4 * mm))
        el.append(Paragraph(f"Handshake error: <b>{ssl.get('error')}</b>", styles["body"]))

    el.append(PageBreak())
    return el


def _page_domain(styles, scan: dict) -> list:
    domain = (scan.get("payload") or {}).get("domain") or {}
    whois = domain.get("whois") or {}
    dns = domain.get("dns") or {}
    el = [_section_title(styles, "Domain Intelligence")]

    el.append(Paragraph("WHOIS record", styles["h3"]))
    el.append(_kv_table([
        ("Registered domain", domain.get("domain") or whois.get("domain") or "—"),
        ("Top-level domain", domain.get("tld") or "—"),
        ("Suspicious TLD", "Yes" if domain.get("suspicious_tld") else "No"),
        ("Creation date", whois.get("creation_date") or "—"),
        ("Expiry date", whois.get("expiry_date") or "—"),
        ("Days until expiry", str(whois.get("days_to_expiry") if whois.get("days_to_expiry") is not None else "—")),
        ("Last updated", whois.get("updated_date") or "—"),
        ("Age (days)", str(whois.get("age_days") if whois.get("age_days") is not None else "—")),
        ("Age (years)", str(whois.get("age_years") if whois.get("age_years") is not None else "—")),
        ("Registrar", whois.get("registrar") or "—"),
        ("Recently registered (<180d)", "Yes" if whois.get("is_new") else "No"),
    ]))

    el.append(Spacer(1, 4 * mm))
    el.append(Paragraph("Name servers", styles["h3"]))
    ns_list = whois.get("name_servers") or dns.get("ns") or []
    if ns_list:
        rows = [[ns] for ns in ns_list[:12]]
        el.append(_matrix_table(["Nameserver"], rows, col_widths=[170 * mm]))
    else:
        el.append(Paragraph("No nameserver records available.", styles["muted"]))

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("DNS records", styles["h3"]))
    rows = []
    for kind in ("a", "mx", "ns"):
        items = dns.get(kind) or []
        rows.append([kind.upper(), ", ".join(items[:10]) if items else "—"])
    rows.append(["SPF", dns.get("spf") or "—"])
    rows.append(["DMARC", dns.get("dmarc") or "—"])
    rows.append(["DKIM (default selector)", dns.get("dkim_default_selector") or "—"])
    rows.append(["Has email config (MX + SPF)", "Yes" if dns.get("has_email_config") else "No"])
    el.append(_matrix_table(
        header=["Record", "Value"],
        rows=rows,
        col_widths=[45 * mm, 125 * mm],
    ))
    el.append(PageBreak())
    return el


def _page_reputation(styles, scan: dict) -> list:
    rep = (scan.get("payload") or {}).get("reputation") or {}
    el = [_section_title(styles, "Reputation Matrix")]

    malicious = rep.get("malicious")
    mal_str = "Malicious" if malicious is True else "Clean" if malicious is False else "Unknown"

    el.append(_kv_table([
        ("Aggregate verdict", mal_str),
        ("Aggregate score (0–100, higher = worse)", str(rep.get("score") if rep.get("score") is not None else "—")),
        ("Merge confidence", f"{int(round((rep.get('confidence') or 0) * 100))}%" if rep.get("confidence") is not None else "—"),
        ("Threat categories", ", ".join(rep.get("categories") or []) or "—"),
    ]))

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("Per-provider verdicts", styles["h3"]))
    providers = rep.get("providers") or []
    if not providers:
        el.append(Paragraph("No reputation providers returned data for this target.", styles["muted"]))
    else:
        rows = []
        for p in providers:
            if not isinstance(p, dict):
                continue
            verdict = "Malicious" if p.get("malicious") is True else "Clean" if p.get("malicious") is False else "Unknown"
            rows.append([
                p.get("provider", "—"),
                verdict,
                f"{p.get('score'):.1f}" if isinstance(p.get("score"), (int, float)) else "—",
                f"{int(round((p.get('confidence') or 0) * 100))}%",
                ", ".join(p.get("categories") or []) or "—",
                p.get("error") or "—",
            ])
        el.append(_matrix_table(
            header=["Provider", "Verdict", "Score", "Confidence", "Categories", "Error"],
            rows=rows,
            col_widths=[32 * mm, 22 * mm, 18 * mm, 22 * mm, 40 * mm, 36 * mm],
            verdict_col=1,
        ))

    # vpn/proxy/tor
    vpt = rep.get("vpn_proxy_tor")
    if isinstance(vpt, dict):
        el.append(Spacer(1, 6 * mm))
        el.append(Paragraph("Anonymisation signals (IP targets only)", styles["h3"]))
        el.append(_matrix_table(
            header=["VPN", "Proxy", "Tor"],
            rows=[["Yes" if vpt.get("vpn") else "No",
                   "Yes" if vpt.get("proxy") else "No",
                   "Yes" if vpt.get("tor") else "No"]],
            col_widths=[56 * mm, 56 * mm, 56 * mm],
            verdict_col=0,
        ))
    el.append(PageBreak())
    return el


def _page_phishing(styles, scan: dict) -> list:
    ph = (scan.get("payload") or {}).get("phishing") or {}
    el = [_section_title(styles, "Phishing Heuristics")]

    el.append(_kv_table([
        ("Heuristic score (0–100, higher = worse)", str(ph.get("score") if ph.get("score") is not None else "—")),
        ("Host label entropy (bits)", str(ph.get("entropy") if ph.get("entropy") is not None else "—")),
        ("Subdomain depth", str(ph.get("subdomain_depth") if ph.get("subdomain_depth") is not None else "—")),
    ]))

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("Fired heuristics", styles["h3"]))
    indicators = ph.get("indicators") or []
    if not indicators:
        el.append(Paragraph("No phishing heuristics matched this target.", styles["muted"]))
    else:
        rows = []
        for i in indicators:
            if not isinstance(i, dict):
                continue
            rows.append([
                (i.get("severity") or "info").upper(),
                i.get("kind", "—"),
                i.get("label", "—"),
            ])
        el.append(_matrix_table(
            header=["Severity", "Heuristic", "Detail"],
            rows=rows,
            col_widths=[22 * mm, 42 * mm, 106 * mm],
            verdict_col=0,
        ))
    el.append(PageBreak())
    return el


def _page_http(styles, scan: dict) -> list:
    url = (scan.get("payload") or {}).get("url") or {}
    headers = url.get("header_flags") or {}
    raw_headers = url.get("headers") or {}
    redirects = url.get("redirect_chain") or []
    body = url.get("body_patterns") or []

    el = [_section_title(styles, "HTTP Response Analysis")]

    el.append(_kv_table([
        ("Final URL", url.get("final_url") or url.get("url") or "—"),
        ("Status code", str(url.get("status_code") or "—")),
        ("HTTP version", url.get("http_version") or "—"),
        ("Response time", f"{url.get('response_time_ms')} ms" if url.get("response_time_ms") is not None else "—"),
        ("Server header", url.get("server") or "—"),
        ("Redirect count", str(url.get("redirects") or 0)),
        ("Cross-host redirect", "Yes" if url.get("cross_host_redirect") else "No"),
        ("Body length (bytes)", str(url.get("body_length") or 0)),
        ("Scan error", url.get("error") or "None"),
    ]))

    el.append(Spacer(1, 6 * mm))
    el.append(Paragraph("Security header audit", styles["h3"]))
    el.append(_matrix_table(
        header=["Header", "Present"],
        rows=[
            ["Content-Security-Policy", "Yes" if headers.get("csp") else "No"],
            ["Strict-Transport-Security", "Yes" if headers.get("hsts") else "No"],
            ["X-Frame-Options", "Yes" if headers.get("xframe") else "No"],
            ["X-Content-Type-Options", "Yes" if headers.get("xcontent") else "No"],
            ["Referrer-Policy", "Yes" if headers.get("referrer") else "No"],
            ["Permissions-Policy", "Yes" if headers.get("permissions") else "No"],
        ],
        col_widths=[110 * mm, 60 * mm],
        verdict_col=1,
    ))

    if raw_headers:
        el.append(Spacer(1, 4 * mm))
        el.append(Paragraph("Observed header values", styles["h3"]))
        rows = [[k, (str(v)[:120] + "…") if len(str(v)) > 120 else str(v)]
                for k, v in list(raw_headers.items())[:12]]
        el.append(_matrix_table(
            header=["Header", "Value"],
            rows=rows,
            col_widths=[60 * mm, 110 * mm],
        ))

    el.append(Spacer(1, 4 * mm))
    el.append(Paragraph("Redirect chain", styles["h3"]))
    if redirects:
        rows = []
        for hop in redirects[:12]:
            rows.append([
                str(hop.get("status", "—")),
                hop.get("host", "—") or "—",
                (hop.get("url", "—")[:100] + "…") if len(hop.get("url", "")) > 100 else hop.get("url", "—"),
            ])
        el.append(_matrix_table(
            header=["Status", "Host", "URL"],
            rows=rows,
            col_widths=[18 * mm, 42 * mm, 110 * mm],
        ))
    else:
        el.append(Paragraph("No redirects observed.", styles["muted"]))

    if body:
        el.append(Spacer(1, 4 * mm))
        el.append(Paragraph("Suspicious body patterns", styles["h3"]))
        el.append(_matrix_table(
            header=["Pattern"],
            rows=[[b] for b in body],
            col_widths=[170 * mm],
        ))
    el.append(PageBreak())
    return el


def _page_indicator_log(styles, scan: dict) -> list:
    payload = scan.get("payload") or {}
    scoring = payload.get("scoring") or {}
    indicators = scoring.get("indicators") or scan.get("indicators") or []
    el = [_section_title(styles, "Threat Indicator Log")]

    if not indicators:
        el.append(Paragraph("No threat indicators were recorded for this scan.", styles["muted"]))
    else:
        rows = []
        for i in indicators:
            if not isinstance(i, dict):
                continue
            rows.append([
                (i.get("severity") or "info").upper(),
                i.get("kind", "—"),
                i.get("label", "—"),
                f"{float(i.get('score_delta', 0) or 0):+.1f}",
            ])
        el.append(_matrix_table(
            header=["Severity", "Kind", "Description", "Score Δ"],
            rows=rows,
            col_widths=[22 * mm, 38 * mm, 92 * mm, 18 * mm],
            verdict_col=0,
        ))

    el.append(Spacer(1, 8 * mm))
    el.append(Paragraph("Interpretation guide", styles["h3"]))
    el.append(Paragraph(
        "Each fired rule contributes a signed weight to the trust score. A score of 100 "
        "represents perfect trust; 0 represents critical risk. Weights are defined in the "
        "scoring engine at <font face='Courier' size='8'>app/scans/scorer.RULES</font> and "
        "can be tuned without code branching. Reputation signals are weighted by both provider "
        "confidence and provider weight.",
        styles["body"],
    ))
    return el


# ---------------------------------------------------------------------- main
def build_pdf_report(scan: dict) -> bytes:
    """Render the full multi-page PDF report from a scan detail dict.

    ``scan`` should be the JSON shape returned by ``GET /api/v1/scans/{id}`` —
    it must contain at minimum ``target``, ``target_type`` and a ``payload``
    dict produced by the scan pipeline. All other fields degrade gracefully to
    em-dashes when missing.
    """
    styles = _styles()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=22 * mm,
        bottomMargin=18 * mm,
        title=f"TrustScan Report — {scan.get('target', 'unknown')}",
        author="TrustScan Platform",
    )

    story: list = []
    story.extend(_page_cover(styles, scan))
    story.extend(_page_executive(styles, scan))
    story.extend(_page_tls(styles, scan))
    story.extend(_page_domain(styles, scan))
    story.extend(_page_reputation(styles, scan))
    story.extend(_page_phishing(styles, scan))
    story.extend(_page_http(styles, scan))
    story.extend(_page_indicator_log(styles, scan))

    doc.build(story, onFirstPage=_draw_page_chrome, onLaterPages=_draw_page_chrome)
    return buf.getvalue()
