"""FastAPI auth dependencies."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_access
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.database.session import get_db
from app.models.user import User
from app.security.jwt_denylist import is_revoked


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("Missing bearer token.")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access(token)

    jti = payload.get("jti")
    if jti and await is_revoked(jti):
        raise UnauthorizedError("Token has been revoked.")

    sub = payload.get("sub")
    if not sub:
        raise UnauthorizedError("Token subject missing.")
    result = await db.execute(select(User).where(User.id == sub))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise UnauthorizedError("User not found.")
    return user


async def get_optional_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    if not authorization:
        return None
    try:
        return await get_current_user(authorization=authorization, db=db)
    except UnauthorizedError:
        return None


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise ForbiddenError("Admin only.")
    return user
