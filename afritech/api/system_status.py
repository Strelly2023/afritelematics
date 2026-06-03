"""Runtime system-status surface for the controlled pilot API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter


def build_system_status_router() -> APIRouter:
    """Build the runtime status router."""

    router = APIRouter()

    @router.get("/v1/system/status")
    def system_status() -> dict[str, Any]:
        return {
            "status": "active",
            "service": "AfriTech Deterministic MVP Pipeline",
            "classification": "controlled_pilot_api",
            "product_ready": False,
            "docs": "/docs",
            "event_ingestion": "/v1/events",
            "trace_api": "/v1/traces",
        }

    return router