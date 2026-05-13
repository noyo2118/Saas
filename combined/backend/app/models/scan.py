"""Scan + related intelligence records."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPKMixin


class Scan(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "scans"

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    target: Mapped[str] = mapped_column(String(2048), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(16), index=True, nullable=False)
    normalized_target: Mapped[str] = mapped_column(String(2048), index=True, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="queued", index=True, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    trust_score: Mapped[float | None] = mapped_column(Float, index=True, nullable=True)
    fraud_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    threat_level: Mapped[str | None] = mapped_column(String(16), index=True, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict: Mapped[str | None] = mapped_column(String(16), nullable=True)

    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User | None"] = relationship(back_populates="scans")  # noqa: F821
    result: Mapped["ScanResult | None"] = relationship(
        back_populates="scan", uselist=False, cascade="all, delete-orphan",
    )
    ai_report: Mapped["AIReport | None"] = relationship(
        back_populates="scan", uselist=False, cascade="all, delete-orphan",
    )
    indicators: Mapped[list["ThreatIndicator"]] = relationship(  # noqa: F821
        back_populates="scan", cascade="all, delete-orphan",
    )


class ScanResult(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "scan_results"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), index=True, nullable=False, unique=True
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="result")


class AIReport(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "ai_reports"

    scan_id: Mapped[str] = mapped_column(
        ForeignKey("scans.id", ondelete="CASCADE"), index=True, nullable=False, unique=True
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    exec_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    remediation: Mapped[str | None] = mapped_column(Text, nullable=True)

    tokens_in: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scan: Mapped["Scan"] = relationship(back_populates="ai_report")
