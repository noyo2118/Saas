"""Declarative base + UUID / timestamp mixins for SQLAlchemy 2.0."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:  # noqa: N805
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()
        return name if name.endswith("s") else name + "s"


class UUIDPKMixin:
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=new_uuid, index=True
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False,
    )
