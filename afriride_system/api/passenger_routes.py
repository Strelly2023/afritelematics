"""Passenger HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from afriride_system.api.dispatcher_adapter import get_gateway
from afriride_system.api.auth import claims_from_request
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
from afritech.afriprogramming.rbac import evaluate_rbac_access

router = APIRouter()


@router.post("/request-ride")
def request_ride(
    payload: RequestRide,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        command = payload.model_dump()
        log_command("request_ride", command)
        _enforce_ride_access(
            request,
            permission="ride.request",
            actor_id=command["passenger_id"],
            owner_id=command["passenger_id"],
        )
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
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        ride = gateway.dispatcher.rides.get(ride_id)
        if ride is None:
            raise AfriRidePhase1Error("ride_not_found")
        claims = claims_from_request(request)
        permission = "ride.view.own"
        owner_id = ride.passenger_id
        assigned_driver_id = None
        if claims is not None and ride.assigned_driver and claims.sub == ride.assigned_driver:
            permission = "ride.view.assigned"
            owner_id = None
            assigned_driver_id = ride.assigned_driver
        _enforce_ride_access(
            request,
            permission=permission,
            actor_id=claims.sub if claims is not None else None,
            owner_id=owner_id,
            assigned_driver_id=assigned_driver_id,
            privileged_roles=("ADMIN", "DISPATCHER", "FLEET_OWNER"),
        )
        result = gateway.passenger.status(ride_id)
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return success(result)


@router.post("/cancel")
def cancel_ride(
    payload: CancelRide,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        command = payload.model_dump()
        log_command("cancel_ride", command)
        _enforce_ride_access(
            request,
            permission="ride.cancel.own",
            actor_id=command["passenger_id"],
            owner_id=command["passenger_id"],
        )
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


def _enforce_ride_access(
    request: Request | None,
    *,
    permission: str,
    actor_id: str | None,
    owner_id: str | None = None,
    assigned_driver_id: str | None = None,
    privileged_roles: tuple[str, ...] = ("ADMIN",),
) -> None:
    claims = claims_from_request(request)
    if claims is None:
        return
    decision = evaluate_rbac_access(
        role=claims.role,
        permission=permission,
        actor_id=actor_id or claims.sub,
        owner_id=owner_id,
        assigned_driver_id=assigned_driver_id,
        privileged_roles=privileged_roles,
    )
    if not decision["allowed"]:
        raise HTTPException(status_code=403, detail=decision["reason"])
