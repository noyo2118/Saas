"""JWT + refresh-token helpers (HS256).

Hardening features:
    - ``jti`` on every access token → compatible with the runtime denylist.
    - ``iss`` + ``aud`` claims, verified on decode.
    - Leeway 0 — no clock-skew grace (tokens are already 30 min).
    - Constant-time comparisons where needed.
    - Refresh tokens are long opaque URL-safe secrets; we only store SHA-256
      digests at rest.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(*, sub: str, extra: dict[str, Any] | None = None) -> tuple[str, int, str]:
    """Mint an access token. Returns (token, ttl_seconds, jti).

    The jti is returned so the caller can stash it on the session row and
    revoke it later by adding it to the JWT denylist.
    """
    ttl = settings.JWT_ACCESS_TTL_MIN * 60
    jti = uuid.uuid4().hex
    payload: dict[str, Any] = {
        "sub": sub,
        "iat": int(_now().timestamp()),
        "nbf": int(_now().timestamp()),
        "exp": int((_now() + timedelta(seconds=ttl)).timestamp()),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "jti": jti,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return token, ttl, jti


def create_refresh_token() -> tuple[str, str, datetime]:
    """Return (plaintext_token, sha256_hash, expires_at). Store the hash, give out the plaintext."""
    raw = secrets.token_urlsafe(48)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    expires_at = _now() + timedelta(days=settings.JWT_REFRESH_TTL_DAYS)
    return raw, digest, expires_at


def hash_refresh(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def decode_access(token: str) -> dict[str, Any]:
    """Decode and verify — raises UnauthorizedError on any problem."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALG],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
            leeway=0,
            options={"require": ["exp", "iat", "sub", "iss", "aud", "jti"]},
        )
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Access token expired.")
    except jwt.InvalidAudienceError:
        raise UnauthorizedError("Invalid audience.")
    except jwt.InvalidIssuerError:
        raise UnauthorizedError("Invalid issuer.")
    except jwt.MissingRequiredClaimError:
        raise UnauthorizedError("Token missing required claim.")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid access token.")
    if payload.get("type") != "access":
        raise UnauthorizedError("Wrong token type.")
    return payload


def constant_time_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))
