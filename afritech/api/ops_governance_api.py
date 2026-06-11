"""Operator observability and audit dashboard API surfaces."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.ops_dashboard import build_audit_dashboard, build_observability_dashboard


def build_ops_governance_router() -> APIRouter:
    router = APIRouter(tags=["ops-governance"])

    @router.get("/v1/ops/observability/dashboard")
    def observability_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return build_observability_dashboard()

    @router.get("/v1/ops/audit/dashboard")
    def audit_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        return build_audit_dashboard()

    return router


__all__ = ["build_ops_governance_router"]
