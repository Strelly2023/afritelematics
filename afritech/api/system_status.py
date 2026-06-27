"""Runtime system-status surface for the controlled pilot API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from afritech.core_platform.settlement import build_settlement_status
from afritech.core_platform.stack import build_novatech_stack_readiness


def build_system_status_router() -> APIRouter:
    """Build the runtime status router."""

    router = APIRouter()

    @router.get("/v1/system/status")
    def system_status() -> dict[str, Any]:
        return {
            "status": "active",
            "service": "NovaTech Deterministic MVP Pipeline",
            "classification": "controlled_pilot_api",
            "product_ready": False,
            "docs": "/docs",
            "event_ingestion": "/v1/events",
            "trace_api": "/v1/traces",
            "deployment": {
                "stack": build_novatech_stack_readiness(),
                "settlement": build_settlement_status(),
            },
        }

    return router
