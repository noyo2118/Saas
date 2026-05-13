"""Typed cache key namespaces.

Centralising key formats prevents stringly-typed bugs and makes invalidation
trivial — grep for ``ns.scan(...)`` finds every read/write.
"""
from __future__ import annotations

import hashlib


def _h(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:24]  # noqa: S324 - not for auth


class ns:  # noqa: N801 - namespace sentinel
    """All cache keys are built through these helpers."""

    @staticmethod
    def scan(target: str) -> str:
        return f"ts:scan:{_h(target.lower())}"

    @staticmethod
    def reputation(provider: str, target: str) -> str:
        return f"ts:rep:{provider}:{_h(target.lower())}"

    @staticmethod
    def dns(kind: str, domain: str) -> str:
        return f"ts:dns:{kind}:{domain.lower()}"

    @staticmethod
    def whois(domain: str) -> str:
        return f"ts:whois:{domain.lower()}"

    @staticmethod
    def ai(scan_id: str) -> str:
        return f"ts:ai:{scan_id}"

    @staticmethod
    def session(token_hash: str) -> str:
        return f"ts:sess:{token_hash}"

    @staticmethod
    def otp_cooldown(email: str) -> str:
        return f"ts:otpcd:{email.lower()}"

    @staticmethod
    def rate_limit(bucket: str, identity: str) -> str:
        return f"ts:rl:{bucket}:{identity}"

    @staticmethod
    def ws_state(channel: str) -> str:
        return f"ts:ws:{channel}"
