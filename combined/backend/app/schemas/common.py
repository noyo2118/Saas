"""Shared Pydantic response wrappers."""
from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    trace_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class Envelope(BaseModel, Generic[T]):
    ok: bool = True
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


class MessageResponse(BaseModel):
    ok: bool = True
    message: str
