"""Aggregate v1 router."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import admin, auth, scans, users, ws
from app.api.v1.intelligence import (
    domain_router,
    intelligence_router,
    ip_router,
    reputation_router,
    url_router,
)

api_v1_router = APIRouter()

api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(scans.router)
api_v1_router.include_router(intelligence_router)
api_v1_router.include_router(url_router)
api_v1_router.include_router(ip_router)
api_v1_router.include_router(domain_router)
api_v1_router.include_router(reputation_router)
api_v1_router.include_router(admin.router)
api_v1_router.include_router(ws.router)
