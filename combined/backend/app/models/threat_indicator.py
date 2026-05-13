"""Individual threat / trust signals produced by the pipeline."""
from __future__ import annotations

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin


class ThreatIndicator(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "threat_indicators"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), index=True, nullable=False
    )

    kind: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    score_delta: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    scan: Mapped["Scan"] = relationship(back_populates="indicators")  # noqa: F821
