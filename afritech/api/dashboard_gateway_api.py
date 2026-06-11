"""FastAPI read-only gateway surface for the AfriTech dashboard."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.architecture.afritech_dashboard.services import (
    build_dashboard_gateway_overview,
    build_dashboard_gateway_status,
)

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_PATH = ROOT / "afritech/architecture/afritech_dashboard/templates/dashboard.html"


def build_dashboard_gateway_router() -> APIRouter:
    router = APIRouter(tags=["dashboard-gateway"])

    @router.get("/afritech/dashboard/", response_class=HTMLResponse)
    def dashboard_gateway_http() -> str:
        return TEMPLATE_PATH.read_text(encoding="utf-8")

    @router.get("/afritech/dashboard/status")
    def dashboard_gateway_http_status() -> dict[str, object]:
        return build_dashboard_gateway_status()

    @router.get("/v1/dashboard/gateway")
    def dashboard_gateway_overview(
        role: str = "operator",
        ride_id: str = "ride-demo-001",
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, object]:
        return build_dashboard_gateway_overview(role=role, ride_id=ride_id)

    @router.get("/v1/dashboard/gateway/status")
    def dashboard_gateway_status(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, object]:
        return build_dashboard_gateway_status()

    @router.get("/v1/dashboard/gateway/roles/{role}")
    def dashboard_gateway_for_role(
        role: str,
        ride_id: str = "ride-demo-001",
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, object]:
        return build_dashboard_gateway_overview(role=role, ride_id=ride_id)

    @router.get("/v1/dashboard/gateway/context/{ride_id}")
    def dashboard_gateway_context(
        ride_id: str,
        role: str = "operator",
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, object]:
        payload = build_dashboard_gateway_overview(role=role, ride_id=ride_id)
        return {
            "dashboard": payload["dashboard"],
            "role_surface": payload["role_surface"],
            "deep_links": payload["deep_links"],
            "cross_system_context": payload["cross_system_context"],
            "read_only": True,
            "creates_authority": False,
        }

    return router


__all__ = ["build_dashboard_gateway_router"]
