"""Passenger HTTP routes."""

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
from afriride_system.api.schemas import CancelRide, RequestRide
from afriride_system.backend.api_gateway.gateway import AfriRideGateway
from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRidePhase1Error,
)

router = APIRouter()


@router.post("/request-ride")
def request_ride(
    payload: RequestRide,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        command = payload.model_dump()
        log_command("request_ride", command)
        result = run_once(
            idempotency_key,
            lambda: gateway.passenger.request_ride(command),
            fingerprint=command_fingerprint("request_ride", command),
        )
        log_result("request_ride", result)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success(result)


@router.get("/status/{ride_id}")
def ride_status(
    ride_id: str,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        result = gateway.passenger.status(ride_id)
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success(result)


@router.post("/cancel")
def cancel_ride(
    payload: CancelRide,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        command = payload.model_dump()
        log_command("cancel_ride", command)
        result = run_once(
            idempotency_key,
            lambda: gateway.passenger.cancel(command),
            fingerprint=command_fingerprint("cancel_ride", command),
        )
        log_result("cancel_ride", result)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return success(result)
