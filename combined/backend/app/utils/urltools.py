"""URL / domain helpers used across services."""
from __future__ import annotations

import re
from urllib.parse import urlparse

_TWO_PART_TLDS = {
    "co.in", "com.au", "co.uk", "org.uk", "net.au",
    "com.br", "co.za", "co.nz", "com.sg", "co.jp",
    "org.in", "net.in", "gov.in", "edu.au",
}

_SHORTENER_HOSTS = {
    "bit.ly", "tinyurl.com", "t.co", "ow.ly", "is.gd",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorte.st", "adf.ly",
    "goo.gl", "rb.gy", "t.ly",
}

_SUSPICIOUS_TLDS = {
    "zip", "mov", "xyz", "top", "tk", "ml", "ga", "cf",
    "gq", "click", "link", "fit", "rest", "icu", "buzz",
    "loan", "work", "country",
}


def normalize_url(url: str) -> str:
    url = url.strip()
    lower = url.lower()
    if not re.match(r"^[a-z][a-z0-9+.-]*:", lower):
        url = "https://" + url
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    hostname = (parsed.hostname or "").lower()
    port = f":{parsed.port}" if parsed.port else ""
    if hostname.startswith("www."):
        hostname = hostname[4:]
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{scheme}://{hostname}{port}{path}{query}"


def extract_domain(url_or_domain: str) -> str:
    raw = url_or_domain.strip().lower()
    parsed = urlparse(raw if "://" in raw else "https://" + raw)
    host = (parsed.hostname or "").lstrip(".")
    if host.startswith("www."):
        host = host[4:]
    parts = host.split(".")
    if len(parts) >= 3:
        last_two = ".".join(parts[-2:])
        if last_two in _TWO_PART_TLDS:
            return ".".join(parts[-3:])
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def tld_of(domain: str) -> str:
    parts = domain.lower().split(".")
    return parts[-1] if parts else ""


def is_url_shortener(host: str) -> bool:
    return host.lower().lstrip(".").lstrip("www.") in _SHORTENER_HOSTS


def is_suspicious_tld(domain: str) -> bool:
    return tld_of(domain) in _SUSPICIOUS_TLDS
