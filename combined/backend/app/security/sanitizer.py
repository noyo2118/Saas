"""Input sanitizers for user-supplied targets."""
from __future__ import annotations

import re
from urllib.parse import urlparse

from app.core.config import settings
from app.core.exceptions import InvalidTargetError

_HTTP_SCHEME_RX = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)
_CTRL_RX = re.compile(r"[\x00-\x1f\x7f]")


def sanitize_url(url: str) -> str:
    """Trim + validate a candidate URL, add https:// if missing."""
    if not isinstance(url, str):
        raise InvalidTargetError("Target must be a string.")
    url = url.strip()
    if not url:
        raise InvalidTargetError("Empty target.")
    if len(url) > settings.MAX_URL_LENGTH:
        raise InvalidTargetError("Target URL is too long.")
    if _CTRL_RX.search(url):
        raise InvalidTargetError("Target contains control characters.")
    if not _HTTP_SCHEME_RX.match(url):
        url = "https://" + url
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in settings.ALLOWED_SCHEMES:
        raise InvalidTargetError(f"Scheme '{scheme}' is not allowed.")
    if not parsed.hostname:
        raise InvalidTargetError("Target is missing a hostname.")
    return url


def detect_target_type(raw: str) -> str:
    """Guess the target kind — returns one of: 'ip' | 'domain' | 'url' | 'email'."""
    raw = raw.strip()
    if "@" in raw and not raw.startswith("http"):
        return "email"
    try:
        import ipaddress

        ipaddress.ip_address(raw)
        return "ip"
    except ValueError:
        pass
    if raw.startswith("http://") or raw.startswith("https://"):
        return "url"
    if "/" in raw or "?" in raw:
        return "url"
    return "domain"
