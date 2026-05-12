"""SSRF protection — validate scan targets before we touch them.

Blocks:
    - non-HTTP(S) schemes (file://, gopher://, ftp://, data:, javascript:, ...)
    - localhost / loopback (127.0.0.0/8, ::1)
    - RFC1918 private ranges (10/8, 172.16/12, 192.168/16)
    - link-local (169.254/16)
    - multicast / reserved / 0.0.0.0
    - cloud metadata endpoints (169.254.169.254, metadata.google.internal, etc.)
    - URLs exceeding max length
    - hostnames that resolve to any of the above
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket
from typing import Iterable
from urllib.parse import urlparse

from app.core.config import settings
from app.core.exceptions import InvalidTargetError, SSRFBlockedError

_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",
    "metadata",
    "instance-data",
    "metadata.aws",
}

_BLOCKED_METADATA_IPS = {
    "169.254.169.254",  # AWS / GCP / Azure IMDS
    "100.100.100.200",  # Alibaba
    "fd00:ec2::254",
}


def _is_blocked_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return True
    if addr.is_loopback and settings.BLOCK_LOCALHOST:
        return True
    if settings.BLOCK_PRIVATE_IPS and (
        addr.is_private
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
        or addr.is_unspecified
    ):
        return True
    if ip in _BLOCKED_METADATA_IPS:
        return True
    return False


async def _resolve_all(hostname: str) -> list[str]:
    """Resolve all A/AAAA records for the hostname. Returns [] on failure."""
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return list({info[4][0] for info in infos})


async def assert_safe_url(url: str) -> str:
    """Raise SSRFBlockedError if the URL targets an internal/private host.

    Returns the URL unchanged on success.
    """
    if not url or not isinstance(url, str):
        raise InvalidTargetError("Empty target URL.")
    if len(url) > settings.MAX_URL_LENGTH:
        raise InvalidTargetError(f"URL exceeds {settings.MAX_URL_LENGTH} characters.")

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    if scheme not in settings.ALLOWED_SCHEMES:
        raise SSRFBlockedError(f"Scheme '{scheme}' is not allowed.")

    hostname = (parsed.hostname or "").lower().strip()
    if not hostname:
        raise InvalidTargetError("URL is missing a hostname.")
    if hostname in _BLOCKED_HOSTNAMES:
        raise SSRFBlockedError("Target hostname is not allowed.")

    # If literal IP -> validate directly.
    try:
        ipaddress.ip_address(hostname)
        if _is_blocked_ip(hostname):
            raise SSRFBlockedError("Target IP is in a reserved/private range.")
        return url
    except ValueError:
        pass

    # Resolve + validate every address.
    addresses = await _resolve_all(hostname)
    if not addresses:
        # Let the scanner handle DNS failure — don't fail hard here.
        return url
    for ip in addresses:
        if _is_blocked_ip(ip):
            raise SSRFBlockedError(
                "Target resolves to a private, loopback, or reserved IP range."
            )
    return url


def validate_ip_target(ip: str) -> str:
    """Used by the /ip endpoint — reject private/reserved IP lookups."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError as e:
        raise InvalidTargetError(f"'{ip}' is not a valid IP address.") from e
    if _is_blocked_ip(str(addr)):
        raise SSRFBlockedError("Cannot analyse private/reserved IP addresses.")
    return str(addr)


def is_safe_hosts(addresses: Iterable[str]) -> bool:
    return all(not _is_blocked_ip(a) for a in addresses)
