"""Request/response models for scans."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ScanRequest(BaseModel):
    target: str = Field(..., min_length=1, max_length=2048, description="URL, domain, IP, or email")


class ScanSummary(BaseModel):
    id: str
    target: str
    target_type: str
    normalized_target: str
    status: str
    trust_score: Optional[float] = None
    fraud_probability: Optional[float] = None
    threat_level: Optional[str] = None
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class IndicatorOut(BaseModel):
    kind: str
    label: str
    severity: str
    score_delta: float
    description: Optional[str] = None


class AIReportOut(BaseModel):
    provider: str
    model: Optional[str] = None
    summary: Optional[str] = None
    exec_summary: Optional[str] = None
    risk_description: Optional[str] = None
    remediation: Optional[str] = None


class ScanDetail(ScanSummary):
    payload: dict[str, Any] = Field(default_factory=dict)
    indicators: list[IndicatorOut] = Field(default_factory=list)
    ai_report: Optional[AIReportOut] = None
