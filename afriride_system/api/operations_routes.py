"""Phase 3 operations and explainable AI dispatch routes."""

from __future__ import annotations

from collections import deque
from threading import RLock
from typing import Any
from uuid import uuid4
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from afriride_system.api.dependencies.runtime import get_gateway
from afriride_system.api.idempotency import (
    IdempotencyConflict,
    command_fingerprint,
    run_once,
)
from afriride_system.integration.websocket_gateway.mobility_hub import mobility_hub
from afriride_system.operations.intelligent_dispatch import (
    DispatchCandidate,
    WeightedDispatchEngine,
    fleet_analytics,
    operational_alerts,
)
from afriride_system.operations.fleet_twin import build_fleet_twin
from afriride_system.observability.enterprise import enterprise_dashboard
from afriride_system.services.system_service import SystemService
from afriride_system.api.dependencies.runtime import get_trace_log

router = APIRouter(prefix="/v1/operations", tags=["operations-intelligence"])
_engine = WeightedDispatchEngine()
_decisions: deque[dict[str, Any]] = deque(maxlen=5_000)
_lock = RLock()


class CandidatePayload(BaseModel):
    driver_id: str = Field(min_length=1)
    distance_km: float = Field(ge=0)
    traffic_factor: float = Field(default=1, ge=0.1, le=10)
    driver_rating: float = Field(ge=0, le=5)
    vehicle_type: str = Field(min_length=1)
    acceptance_rate: float = Field(ge=0, le=1)
    trust_score: float = Field(ge=0, le=100)
    battery_level: float = Field(ge=0, le=100)
    estimated_arrival_minutes: float = Field(ge=0, le=240)
    surge_demand: float = Field(default=0, ge=0, le=1)
    online: bool = True
    device_trusted: bool = True
    open_safety_incidents: int = Field(default=0, ge=0)
    fraud_risk_score: float = Field(default=0, ge=0, le=1)
    region_id: str = "ug-kla"
    country_compliant: bool = True


class DispatchOptimizationRequest(BaseModel):
    ride_id: str = Field(min_length=1)
    requested_vehicle_type: str = Field(min_length=1)
    candidates: list[CandidatePayload] = Field(min_length=1, max_length=500)
    trace_id: str | None = None
    region_id: str = "ug-kla"


class DistressSignalRequest(BaseModel):
    rider_id: str = Field(min_length=1)
    ride_id: str = Field(min_length=1)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    signal: str = Field(pattern="^(sos|silent_sos|unsafe_driver|medical)$")
    details: str | None = Field(default=None, max_length=1000)


class IncidentActionRequest(BaseModel):
    action: str = Field(
        pattern="^(acknowledge|driver_verified|rider_verified|sos_dispatched|resolve)$"
    )


def _evaluate(payload: DispatchOptimizationRequest) -> dict[str, Any]:
    regional_candidates = [
        candidate for candidate in payload.candidates
        if candidate.region_id == payload.region_id and candidate.country_compliant
    ]
    if not regional_candidates:
        raise HTTPException(status_code=409, detail="no_candidates_in_dispatch_region")
    decision = _engine.rank(
        [
            DispatchCandidate(
                **candidate.model_dump(exclude={"region_id", "country_compliant"})
            )
            for candidate in regional_candidates
        ],
        requested_vehicle_type=payload.requested_vehicle_type,
        trace_id=payload.trace_id or f"dispatch-{uuid4().hex}",
    )
    decision["ride_id"] = payload.ride_id
    decision["region_id"] = payload.region_id
    decision["fleet_analytics"] = fleet_analytics(
        [
            DispatchCandidate(
                **candidate.model_dump(exclude={"region_id", "country_compliant"})
            )
            for candidate in regional_candidates
        ]
    )
    decision["alerts"] = operational_alerts(
        [
            DispatchCandidate(
                **candidate.model_dump(exclude={"region_id", "country_compliant"})
            )
            for candidate in regional_candidates
        ]
    )
    with _lock:
        _decisions.append(decision)
    mobility_hub.publish(
        "DISPATCH_OPTIMIZED",
        targets={f"ride:{payload.ride_id}", "role:dispatcher"},
        partition=f"ride:{payload.ride_id}",
        trace_id=decision["trace_id"],
        data={
            "ride_id": payload.ride_id,
            "selected_driver_id": decision["selected_driver_id"],
            "selected_score": decision["selected_score"],
            "automation": decision["automation"],
            "region_id": payload.region_id,
        },
    )
    mobility_hub.publish(
        "FLEET_ANALYTICS_UPDATED",
        targets={"role:dispatcher", "role:operator"},
        partition="operations:fleet",
        trace_id=decision["trace_id"],
        data=decision["fleet_analytics"],
    )
    for alert in decision["alerts"]:
        mobility_hub.publish(
            "OPERATIONAL_ALERT",
            targets={"role:dispatcher", "role:operator", f"actor:{alert['driver_id']}"},
            partition="operations:alerts",
            trace_id=decision["trace_id"],
            data=alert,
        )
    return decision


@router.post("/dispatch/optimize")
def optimize_dispatch(payload: DispatchOptimizationRequest) -> dict[str, Any]:
    return _evaluate(payload)


@router.post("/dispatch/execute")
def execute_dispatch(
    payload: DispatchOptimizationRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway=Depends(get_gateway),
) -> dict[str, Any]:
    try:
        return run_once(
            idempotency_key,
            lambda: _execute_dispatch(payload, idempotency_key, gateway),
            fingerprint=command_fingerprint(
                "phase3_weighted_dispatch", payload.model_dump(mode="json")
            ),
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


def _execute_dispatch(payload, idempotency_key, gateway) -> dict[str, Any]:
    decision = _evaluate(payload)
    if not decision["automation"]["eligible"]:
        raise HTTPException(status_code=409, detail="dispatch_requires_operator_review")
    driver_id = decision["selected_driver_id"]
    if not driver_id:
        raise HTTPException(status_code=409, detail="no_eligible_driver")
    try:
        assignment = gateway.driver.accept(
            {"driver_id": driver_id, "ride_id": payload.ride_id}
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {
        "status": "assigned",
        "idempotency_key": idempotency_key,
        "decision": decision,
        "assignment": assignment,
        "authority": "authoritative_dispatcher_accepted",
    }


@router.get("/dashboard")
def operations_dashboard() -> dict[str, Any]:
    with _lock:
        decisions = list(_decisions)
    alerts = [alert for decision in decisions for alert in decision["alerts"]]
    automated = sum(decision["automation"]["eligible"] for decision in decisions)
    return {
        "status": "operational",
        "dispatch": {
            "decisions": len(decisions),
            "automatic_eligible": automated,
            "operator_review": len(decisions) - automated,
            "latest": decisions[-1] if decisions else None,
        },
        "fraud_and_safety": {
            "active_alerts": alerts[-100:],
            "critical_count": sum(alert["severity"] == "critical" for alert in alerts),
        },
        "observability": {
            "decision_retention": _decisions.maxlen,
            "explainability": "factor_contributions_and_policy_gates",
            "automation_authority": "existing_dispatcher_only",
        },
    }


@router.get("/observability")
def observability_dashboard(gateway=Depends(get_gateway), trace_log=Depends(get_trace_log)):
    trust = SystemService(gateway, trace_log).trust_metrics()
    return enterprise_dashboard(gateway, trust)


@router.get("/launch-readiness")
def launch_readiness(gateway=Depends(get_gateway)) -> dict[str, Any]:
    checks = {
        "postgres": gateway.storage.backend == "postgres",
        "redis_realtime": os.environ.get("AFRIRIDE_REALTIME_BACKEND") == "redis",
        "push_delivery": os.environ.get("AFRIRIDE_PUSH_DELIVERY_ENABLED", "").lower() == "true",
        "stripe_live": bool(os.environ.get("STRIPE_SECRET_KEY", "").startswith("sk_live_")),
        "flutterwave_live": bool(os.environ.get("FLUTTERWAVE_SECRET_KEY")),
        "android_production_signing": all(
            os.environ.get(name)
            for name in (
                "AFRIRIDE_ANDROID_KEYSTORE_PATH",
                "AFRIRIDE_ANDROID_KEYSTORE_PASSWORD",
                "AFRIRIDE_ANDROID_KEY_ALIAS",
                "AFRIRIDE_ANDROID_KEY_PASSWORD",
            )
        ),
        "apple_distribution": bool(os.environ.get("ASC_API_KEY_ID")),
    }
    return {
        "status": "ready" if all(checks.values()) else "blocked",
        "checks": checks,
        "blocking": [name for name, passed in checks.items() if not passed],
        "checklist": "docs/operations/AFRIRIDE_PHASE6_PHASE7_LAUNCH.md",
        "authority": "fail_closed_release_gate",
    }


@router.get("/digital-twin")
def digital_twin(gateway=Depends(get_gateway)) -> dict[str, Any]:
    return build_fleet_twin(gateway)


@router.get("/safety/incidents")
def safety_incidents(status: str | None = None, gateway=Depends(get_gateway)) -> dict[str, Any]:
    incidents = gateway.fleet_operations_repository.incidents(status)
    return {"items": list(incidents), "count": len(incidents)}


@router.post("/safety/incidents/{incident_id}/actions")
def incident_action(
    incident_id: str,
    payload: IncidentActionRequest,
    gateway=Depends(get_gateway),
) -> dict[str, Any]:
    try:
        incident = gateway.fleet_operations_repository.transition_incident(
            incident_id, payload.action
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    mobility_hub.publish(
        "SAFETY_WORKFLOW_UPDATED",
        targets={"role:operator", "role:dispatcher"},
        partition="operations:safety",
        data={"action": payload.action, "incident": incident},
    )
    return incident


@router.post("/safety/distress")
def rider_distress(payload: DistressSignalRequest, gateway=Depends(get_gateway)) -> dict[str, Any]:
    incident = gateway.fleet_operations_repository.create_incident(
        idempotency_key=f"distress:{payload.ride_id}:{payload.rider_id}:{payload.signal}",
        incident_type="rider_distress",
        severity="critical",
        workflow="sos_handling",
        evidence=payload.model_dump(mode="json"),
        rider_id=payload.rider_id,
        ride_id=payload.ride_id,
    )
    mobility_hub.publish(
        "SOS_TRIGGERED",
        targets={f"actor:{payload.rider_id}", f"ride:{payload.ride_id}", "role:operator"},
        partition="operations:sos",
        data=incident,
    )
    return {"status": "incident_created", "incident": incident}


@router.post("/safety/sweep")
def safety_sweep(gateway=Depends(get_gateway)) -> dict[str, Any]:
    twin = build_fleet_twin(gateway)
    created = []
    stale_ids = {
        position["driver_id"]
        for position in twin["driver_positions"]
        if position["driver_id"]
        and _position_is_stale(position["captured_at"])
    }
    for driver_id in stale_ids:
        incident = gateway.fleet_operations_repository.create_incident(
            idempotency_key=f"inactivity:{driver_id}:{datetime_bucket()}",
            incident_type="driver_inactivity",
            severity="warning",
            workflow="driver_verification",
            evidence={"last_position": gateway.fleet_operations_repository.telemetry_for(driver_id)},
            driver_id=driver_id,
        )
        created.append(incident)
    return {"evaluated_drivers": len(twin["driver_positions"]), "incidents": created}


def _position_is_stale(timestamp: str) -> bool:
    from datetime import UTC, datetime
    captured = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
    return (datetime.now(UTC) - captured).total_seconds() > 120


def datetime_bucket() -> str:
    from datetime import UTC, datetime
    return datetime.now(UTC).strftime("%Y%m%d%H")
