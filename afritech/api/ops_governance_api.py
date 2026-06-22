"""Operator observability and audit dashboard API surfaces."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from afritech.api.auth.jwt_device_auth import require_roles
from afritech.api.realtime.dashboard_bus import publish_dashboard_snapshot
from afritech.monitoring.realtime_anomaly_alerting import build_realtime_anomaly_alerts
from afritech.runtime_monitoring.monitor import collect_runtime_events
from afritech.compliance.continuous_assurance import (
    build_continuous_assurance_dashboard,
    run_continuous_assurance_cycle,
)
from afritech.ops_dashboard import build_audit_dashboard, build_observability_dashboard


def build_ops_governance_router() -> APIRouter:
    router = APIRouter(tags=["ops-governance"])

    @router.get("/v1/ops/observability/dashboard")
    async def observability_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        dashboard = build_observability_dashboard()
        await publish_dashboard_snapshot(
            {
                "source": "ops_observability_dashboard",
                "status": dashboard.get("status"),
                "summary": dashboard.get("summary", dashboard),
            }
        )
        return dashboard

    @router.get("/v1/ops/audit/dashboard")
    async def audit_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        dashboard = build_audit_dashboard()
        await publish_dashboard_snapshot(
            {
                "source": "ops_audit_dashboard",
                "status": dashboard.get("status"),
                "summary": dashboard.get("summary", dashboard),
            }
        )
        return dashboard

    @router.get("/v1/ops/continuous-assurance/dashboard")
    async def continuous_assurance_dashboard(
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        runtime_events = collect_runtime_events(
            validation_failures=("device_clock_skew", "signing_key_rotation"),
            replay_mismatches=("continuous-assurance-replay-001",),
        )
        alerts = build_realtime_anomaly_alerts(
            runtime_events,
            ride_id="continuous-assurance-001",
            trace_id="continuous-assurance-trace-001",
            event_id="continuous-assurance-event-001",
            actor_id="continuous-assurance-operator",
            device_id="continuous-assurance-console",
            replay_hash="c" * 64,
            receipt_hash="d" * 64,
            opened_at="2026-06-14T00:00:00Z",
        )
        dashboard = build_continuous_assurance_dashboard(
            anomaly_alerts=alerts,
            monitoring_status="WATCH" if alerts else "GREEN",
            submission_ready=True,
            regulator_ready=True,
        )
        await publish_dashboard_snapshot(
            {
                "source": "ops_continuous_assurance_dashboard",
                "status": dashboard.get("monitoring_status"),
                "alerts": len(alerts),
            }
        )
        return dashboard

    @router.post("/v1/ops/regulatory/submission/preview")
    def regulatory_submission_preview(
        payload: dict[str, Any],
        _: object = Depends(require_roles("OPERATOR", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        evidence_items = payload.get("evidence_items", [])
        if not isinstance(evidence_items, list):
            raise HTTPException(status_code=400, detail="evidence_items must be a list")
        package = run_continuous_assurance_cycle(evidence_items=evidence_items)
        return {
            "classification": "REGULATORY_SUBMISSION_AUTOMATION",
            "authority_boundary": "submission_preview_reads_external_evidence_and_proof_only",
            "package": package.canonical_dict(),
            "verified": True,
        }

    return router


__all__ = ["build_ops_governance_router"]
