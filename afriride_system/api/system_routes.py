"""Operator and observability routes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status

from afriride_system.api.auth import JWT
from afriride_system.api.dependencies.runtime import get_gateway, get_trace_log
from afriride_system.services.system_service import SystemService

router = APIRouter(tags=["system"])


def _service() -> SystemService:
    return SystemService(get_gateway(), get_trace_log())


@router.get("/rides/active")
def active_rides() -> dict:
    return _service().active_rides()


@router.get("/system/health")
def system_health() -> dict:
    return _service().system_health()


@router.get("/system/drivers")
def driver_operations() -> dict:
    return _service().driver_operations()


@router.get("/system/replay/health")
def replay_health() -> dict:
    return _service().replay_health()


@router.get("/system/evidence")
def evidence_pipeline() -> dict:
    return _service().evidence_pipeline()


@router.get("/system/evidence/summary")
def evidence_pipeline_summary() -> dict:
    return _service().evidence_pipeline_summary()


@router.get("/system/guards")
def guard_violations() -> dict:
    return _service().guard_violations()


@router.get("/system/guards/summary")
def guard_violations_summary() -> dict:
    return _service().guard_violations_summary()


@router.get("/system/trust-metrics")
def trust_metrics() -> dict:
    return _service().trust_metrics()


@router.get("/system/pilot-metrics")
def pilot_metrics() -> dict:
    return _service().pilot_metrics()


@router.get("/system/trust-sla")
def trust_sla() -> dict:
    return _service().trust_sla()


@router.post("/system/external-verify/{ride_id}")
def external_verify(ride_id: str, payload: dict | None = None) -> dict:
    try:
        return _service().external_verify(ride_id, payload)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc.args[0])) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/system/traces/{ride_id}")
def trace_integrity(ride_id: str) -> dict:
    return _service().trace_integrity(ride_id)


@router.websocket("/ws/system/trust")
async def trust_runtime_stream(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    if token is None:
        authorization = websocket.headers.get("authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[len("Bearer ") :]
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        claims = JWT.verify_token(token)
    except ValueError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if claims.role != "OPERATOR":
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    service = _service()
    try:
        await websocket.send_json(service.trust_stream_payload())
        while True:
            await asyncio.sleep(1)
            await websocket.send_json(service.trust_stream_payload())
    except WebSocketDisconnect:
        return
