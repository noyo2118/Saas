"""/api/v1/users — current user profile management."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import MeOut

router = APIRouter(prefix="/users", tags=["users"])


class UpdateProfileIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)


@router.get("/me", response_model=MeOut)
async def my_profile(user: User = Depends(get_current_user)) -> MeOut:
    return MeOut(
        id=user.id, email=user.email, display_name=user.display_name,
        is_verified=user.is_verified, is_admin=user.is_admin,
    )


@router.patch("/me", response_model=MeOut)
async def update_profile(
    body: UpdateProfileIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MeOut:
    if body.display_name is not None:
        user.display_name = body.display_name
    await db.commit()
    return MeOut(
        id=user.id, email=user.email, display_name=user.display_name,
        is_verified=user.is_verified, is_admin=user.is_admin,
    )
