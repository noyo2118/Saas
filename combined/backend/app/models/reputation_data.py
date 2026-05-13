"""Raw reputation snapshots."""
from __future__ import annotations

from sqlalchemy import JSON, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDPKMixin


class ReputationData(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "reputation_data"

    target: Mapped[str] = mapped_column(String(2048), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), index=True, nullable=False)

    malicious: Mapped[bool | None] = mapped_column(nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
