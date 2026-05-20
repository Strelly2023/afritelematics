"""Driver HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from afriride_system.api.dispatcher_adapter import get_gateway
from afriride_system.api.idempotency import (
    IdempotencyConflict,
    command_fingerprint,
    run_once,
)
from afriride_system.api.logging import log_command, log_result
from afriride_system.api.responses import success
from afriride_system.api.schemas import DriverStatus, RideAction
from afriride_system.backend.api_gateway.gateway import AfriRideGateway
from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRidePhase1Error,
)

router = APIRouter()


@router.post("/status")
def driver_status(
    payload: DriverStatus,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        command = payload.model_dump()
        log_command("driver_status", command)
        result = run_once(
            idempotency_key,
            lambda: gateway.driver.status(command),
            fingerprint=command_fingerprint("driver_status", command),
        )
        log_result("driver_status", result)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return success(result)


@router.get("/requests/{driver_id}")
def driver_requests(
    driver_id: str,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return success(gateway.driver.requests(driver_id))


@router.post("/accept")
def accept_ride(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("accept_ride", gateway.driver.accept, payload, idempotency_key)


@router.post("/start")
def start_trip(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("start_trip", gateway.driver.start, payload, idempotency_key)


@router.post("/complete")
def complete_trip(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("complete_trip", gateway.driver.complete, payload, idempotency_key)


def _driver_action(
    command_name: str,
    action,
    payload: RideAction,
    idempotency_key: str | None,
) -> dict:
    try:
        command = payload.model_dump()
        log_command(command_name, command)
        result = run_once(
            idempotency_key,
            lambda: action(command),
            fingerprint=command_fingerprint(command_name, command),
        )
        log_result(command_name, result)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success(result)
