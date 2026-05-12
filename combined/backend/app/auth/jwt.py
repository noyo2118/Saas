"""JWT + refresh-token helpers (HS256)."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, sub: str, extra: dict[str, Any] | None = None) -> tuple[str, int]:
    ttl = settings.JWT_ACCESS_TTL_MIN * 60
    payload = {
        "sub": sub,
        "iat": int(_now().timestamp()),
        "exp": int((_now() + timedelta(seconds=ttl)).timestamp()),
        "type": "access",
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return token, ttl


def create_refresh_token() -> tuple[str, str, datetime]:
    """Return (plaintext_token, sha256_hash, expires_at). Store the hash, give out the plaintext."""
    raw = secrets.token_urlsafe(48)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    expires_at = _now() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    return raw, digest, expires_at


def hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decode_access(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Access token expired.")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid access token.")
    if payload.get("type") != "access":
        raise UnauthorizedError("Wrong token type.")
    return payload


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
