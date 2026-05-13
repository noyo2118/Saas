"""/api/v1/auth — email OTP login flow with brute-force protection."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.auth.email import send_otp_email
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_access,
    hash_refresh,
)
from app.auth.lockout import assert_not_locked, clear_failures, register_failure
from app.auth.otp import request_otp, verify_otp
from app.core.exceptions import OTPInvalidError, UnauthorizedError
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.session import UserSession
from app.models.user import User
from app.schemas.auth import MeOut, OTPRequestIn, OTPVerifyIn, RefreshIn, TokenPair
from app.schemas.common import MessageResponse
from app.security.jwt_denylist import revoke as revoke_jti
from app.utils.time import utcnow

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


@router.post("/otp/request", response_model=MessageResponse)
async def otp_request(
    body: OTPRequestIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Issue a one-time code to the given email address."""
    ip = _client_ip(request)
    await assert_not_locked(str(body.email), ip)
    code = await request_otp(
        db,
        email=str(body.email),
        ip=ip,
        ua=request.headers.get("user-agent"),
    )
    await send_otp_email(str(body.email), code)
    db.add(AuditLog(
        action="otp.request",
        target=str(body.email),
        ip=ip,
        user_agent=(request.headers.get("user-agent") or "")[:512],
        trace_id=getattr(request.state, "trace_id", None),
    ))
    await db.commit()
    # Constant response — never reveal whether the email exists.
    return MessageResponse(ok=True, message="OTP sent if the address is valid.")


@router.post("/otp/verify", response_model=TokenPair)
async def otp_verify(
    body: OTPVerifyIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Verify the OTP, upsert the user, return JWT pair."""
    ip = _client_ip(request)
    identity = str(body.email).lower()
    await assert_not_locked(identity, ip)
    try:
        await verify_otp(db, email=identity, code=body.code)
    except OTPInvalidError:
        await register_failure(identity, ip)
        db.add(AuditLog(
            action="auth.otp_failed",
            target=identity,
            ip=ip,
            trace_id=getattr(request.state, "trace_id", None),
        ))
        await db.commit()
        raise

    # find or create user
    res = await db.execute(select(User).where(User.email == identity))
    user = res.scalars().first()
    if not user:
        user = User(email=identity, is_verified=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        user.is_verified = True

    access, ttl, jti = create_access_token(sub=user.id, extra={"email": user.email})
    raw_refresh, refresh_hash, refresh_exp = create_refresh_token()

    session = UserSession(
        user_id=user.id,
        refresh_token_hash=refresh_hash,
        expires_at=refresh_exp,
        ip=ip,
        user_agent=(request.headers.get("user-agent") or "")[:512],
    )
    db.add(session)
    db.add(AuditLog(
        user_id=user.id,
        action="auth.login",
        ip=ip,
        trace_id=getattr(request.state, "trace_id", None),
    ))
    await db.commit()
    await clear_failures(identity, ip)
    return TokenPair(access_token=access, refresh_token=raw_refresh, expires_in=ttl)


@router.post("/refresh", response_model=TokenPair)
async def refresh(
    body: RefreshIn,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenPair:
    """Rotate the refresh token and mint a new access token."""
    digest = hash_refresh(body.refresh_token)
    res = await db.execute(
        select(UserSession).where(
            UserSession.refresh_token_hash == digest,
            UserSession.is_active.is_(True),
            UserSession.revoked_at.is_(None),
        )
    )
    sess = res.scalars().first()
    if not sess or sess.expires_at < utcnow():
        raise UnauthorizedError("Refresh token invalid or expired.")

    # Rotate: revoke the presented token, issue a new one.
    sess.revoked_at = utcnow()
    sess.is_active = False
    new_raw, new_hash, new_exp = create_refresh_token()
    new_sess = UserSession(
        user_id=sess.user_id,
        refresh_token_hash=new_hash,
        expires_at=new_exp,
        rotated_from=sess.id,
        ip=sess.ip,
        user_agent=sess.user_agent,
    )
    db.add(new_sess)
    access, ttl, _jti = create_access_token(sub=sess.user_id)
    await db.commit()
    return TokenPair(access_token=access, refresh_token=new_raw, expires_in=ttl)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshIn,
    db: AsyncSession = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> MessageResponse:
    """Revoke the refresh token and denylist the access token (if supplied)."""
    digest = hash_refresh(body.refresh_token)
    res = await db.execute(
        select(UserSession).where(UserSession.refresh_token_hash == digest)
    )
    sess = res.scalars().first()
    if sess:
        sess.revoked_at = utcnow()
        sess.is_active = False
        await db.commit()

    # Best-effort: denylist the bearer access token so subsequent calls fail.
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = decode_access(token)
            jti = payload.get("jti")
            exp = int(payload.get("exp") or 0)
            if jti and exp > 0:
                ttl = max(0, exp - int(utcnow().timestamp()))
                if ttl > 0:
                    await revoke_jti(jti, ttl)
        except UnauthorizedError:
            pass

    return MessageResponse(ok=True, message="Logged out.")


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_verified=user.is_verified,
        is_admin=user.is_admin,
    )
