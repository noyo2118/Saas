"""Phishing heuristics engine.

Pure-logic detection (no ML dependency) — designed so an ML classifier can be
slotted in later behind the same ``score_phishing`` interface.
"""
from __future__ import annotations

import math
import re
from typing import Any
from urllib.parse import urlparse

from app.utils.urltools import extract_domain, is_suspicious_tld, is_url_shortener, tld_of

# Known high-value brands — typosquatting often targets these.
_BRAND_KEYWORDS = {
    "google", "apple", "amazon", "microsoft", "facebook", "instagram",
    "paypal", "netflix", "whatsapp", "linkedin", "github", "dropbox",
    "spotify", "outlook", "hotmail", "gmail", "yahoo", "chase", "hdfc",
    "icici", "sbi", "axis", "bankofamerica", "wellsfargo", "citi",
    "coinbase", "binance", "metamask", "kraken",
}

# IDN / homograph — latin look-alike code points.
_HOMOGRAPH_RX = re.compile(r"[а-яА-ЯёЁ]|[\u0430-\u044f]")


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in freq.values())


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            curr.append(min(
                curr[-1] + 1,
                prev[j] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            ))
        prev = curr
    return prev[-1]


def _closest_brand(label: str) -> tuple[str, int] | None:
    candidates = []
    for brand in _BRAND_KEYWORDS:
        d = _levenshtein(label, brand)
        if d <= 2:
            candidates.append((brand, d))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[1])
    return candidates[0]


def score_phishing(url: str) -> dict[str, Any]:
    """Return a phishing heuristic score 0..100 (higher = more suspicious)."""
    parsed = urlparse(url if "://" in url else "https://" + url)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    full_url = url.lower()

    domain = extract_domain(host)
    label = domain.split(".")[0] if domain else ""
    tld = tld_of(domain)

    indicators: list[dict[str, Any]] = []
    score = 0

    # 1. Shorteners
    if is_url_shortener(host):
        score += 20
        indicators.append({"kind": "url_shortener", "severity": "medium", "label": "Link shortener detected"})

    # 2. Suspicious TLD
    if is_suspicious_tld(domain):
        score += 10
        indicators.append({
            "kind": "suspicious_tld", "severity": "medium",
            "label": f"Suspicious TLD .{tld}",
        })

    # 3. IP literal as host
    if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host):
        score += 25
        indicators.append({"kind": "ip_as_host", "severity": "high", "label": "URL uses raw IP instead of domain"})

    # 4. Too many subdomains
    subdomain_depth = host.count(".")
    if subdomain_depth > 4:
        score += 10
        indicators.append({"kind": "deep_subdomain", "severity": "low", "label": f"Deep subdomain ({subdomain_depth} levels)"})

    # 5. Brand keyword in non-apex position (e.g. paypal.bad-site.com)
    for brand in _BRAND_KEYWORDS:
        if brand in host and brand not in label:
            score += 25
            indicators.append({
                "kind": "brand_impersonation",
                "severity": "high",
                "label": f"Brand keyword '{brand}' embedded outside of apex label",
            })
            break

    # 6. Typosquatting near a known brand
    closest = _closest_brand(label) if label else None
    if closest and closest[1] > 0:
        score += 20
        indicators.append({
            "kind": "typosquatting",
            "severity": "high",
            "label": f"Label '{label}' is {closest[1]} edit(s) from '{closest[0]}'",
        })

    # 7. Homoglyphs (cyrillic chars in a mostly-latin host)
    if _HOMOGRAPH_RX.search(host) or "xn--" in host:
        score += 15
        indicators.append({"kind": "homograph", "severity": "high", "label": "Host contains punycode / cyrillic glyphs"})

    # 8. Unusual characters in URL
    if re.search(r"[%@]", full_url[8:]):  # skip scheme
        score += 5
        indicators.append({"kind": "url_obfuscation", "severity": "low", "label": "URL contains obfuscation characters"})
    if "@" in (parsed.netloc or ""):
        score += 20
        indicators.append({"kind": "userinfo_in_url", "severity": "high", "label": "URL contains embedded userinfo (@)"})

    # 9. High entropy label (looks random)
    entropy = _shannon_entropy(label)
    if label and len(label) > 8 and entropy > 3.7:
        score += 10
        indicators.append({
            "kind": "high_entropy", "severity": "medium",
            "label": f"Host label entropy {entropy:.2f} — likely random",
        })

    # 10. Login/verify/secure in path (classic phishing vocabulary)
    phish_words = ("login", "verify", "secure", "account", "update", "confirm", "signin", "wallet", "bank")
    if any(w in path.lower() or w in query.lower() for w in phish_words):
        score += 5
        indicators.append({"kind": "phish_vocabulary", "severity": "low", "label": "URL contains auth-related keywords"})

    score = max(0, min(100, score))
    return {
        "score": score,
        "entropy": round(entropy, 3),
        "indicators": indicators,
        "subdomain_depth": subdomain_depth,
    }
