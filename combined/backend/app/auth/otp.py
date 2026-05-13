"""Email-OTP service — generation, hashing, verification, cooldown."""
from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.keys import ns
from app.cache.redis import cache
from app.core.config import settings
from app.core.exceptions import OTPCooldownError, OTPInvalidError
from app.models.otp_code import OTPCode
from app.telemetry.logger import get_logger
from app.utils.time import utcnow

log = get_logger(__name__)


def _hash_code(email: str, code: str) -> str:
    mac = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        f"{email.lower()}:{code}".encode("utf-8"),
        hashlib.sha256,
    )
    return mac.hexdigest()


def _gen_code(length: int = None) -> str:
    n = length or settings.OTP_LENGTH
    # secrets.randbelow ensures uniform distribution
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


async def request_otp(db: AsyncSession, *, email: str, ip: str | None, ua: str | None) -> str:
    """Create + return a plaintext OTP (caller is responsible for emailing it)."""
    email = email.strip().lower()

    # cooldown
    cd_key = ns.otp_cooldown(email)
    ttl = await cache.ttl(cd_key)
    if ttl > 0:
        raise OTPCooldownError(details={"retry_after": ttl})
    await cache.set_json(cd_key, {"ts": utcnow().isoformat()}, ttl=settings.OTP_RESEND_COOLDOWN_SEC)

    # revoke previous unconsumed OTPs for this email
    await db.execute(
        update(OTPCode)
        .where(OTPCode.email == email, OTPCode.consumed_at.is_(None), OTPCode.is_revoked.is_(False))
        .values(is_revoked=True)
    )

    code = _gen_code()
    expires_at = utcnow() + timedelta(seconds=settings.OTP_TTL_SECONDS)
    row = OTPCode(
        email=email,
        code_hash=_hash_code(email, code),
        expires_at=expires_at,
        max_attempts=settings.OTP_MAX_ATTEMPTS,
        ip=ip,
        user_agent=(ua or "")[:512],
    )
    db.add(row)
    await db.commit()
    log.info("otp_issued", extra={"email": email, "expires_at": expires_at.isoformat()})
    return code


async def verify_otp(db: AsyncSession, *, email: str, code: str) -> bool:
    """Consume the OTP if it matches; raise OTPInvalidError otherwise."""
    email = email.strip().lower()
    stmt = (
        select(OTPCode)
        .where(
            OTPCode.email == email,
            OTPCode.consumed_at.is_(None),
            OTPCode.is_revoked.is_(False),
        )
        .order_by(OTPCode.created_at.desc())
    )
    result = await db.execute(stmt)
    row: OTPCode | None = result.scalars().first()
    if not row:
        raise OTPInvalidError("No active OTP for this address.")

    if row.expires_at < utcnow():
        row.is_revoked = True
        await db.commit()
        raise OTPInvalidError("OTP expired.")

    if row.attempts >= row.max_attempts:
        row.is_revoked = True
        await db.commit()
        raise OTPInvalidError("Too many attempts.")

    row.attempts += 1
    expected = _hash_code(email, code)
    if not hmac.compare_digest(row.code_hash, expected):
        await db.commit()
        raise OTPInvalidError("Incorrect code.")

    row.consumed_at = utcnow()
    await db.commit()
    return True
