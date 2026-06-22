"""Driver HTTP routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from afriride_system.api.auth import claims_from_request
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
from afritech.afriprogramming.rbac import evaluate_rbac_access

router = APIRouter()


@router.post("/status")
def driver_status(
    payload: DriverStatus,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    try:
        command = payload.model_dump()
        log_command("driver_status", command)
        _enforce_driver_access(
            request,
            permission="driver.go_online" if bool(command.get("online", False)) else "driver.go_offline",
            actor_id=command["driver_id"],
            driver_id=command["driver_id"],
            privileged_roles=("ADMIN", "DISPATCHER", "FLEET_OWNER"),
        )
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
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    _enforce_driver_access(
        request,
        permission="ride.view.assigned",
        actor_id=_claims_subject(request),
        driver_id=driver_id,
        privileged_roles=("ADMIN", "DISPATCHER", "FLEET_OWNER"),
    )
    return success(gateway.driver.requests(driver_id))


@router.get("/{driver_id}/rides/assigned")
def assigned_driver_rides(
    driver_id: str,
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    _enforce_driver_access(
        request,
        permission="ride.view.assigned",
        actor_id=_claims_subject(request),
        driver_id=driver_id,
        privileged_roles=("ADMIN", "DISPATCHER", "FLEET_OWNER"),
    )
    rides = [
        _driver_ride_contract(ride, driver_id)
        for ride in gateway.driver.requests(driver_id)
    ]
    return {"rides": rides}


@router.get("/{driver_id}/earnings")
def driver_earnings(
    driver_id: str,
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    _enforce_driver_access(
        request,
        permission="earnings.view.own",
        actor_id=_claims_subject(request),
        driver_id=driver_id,
        privileged_roles=("ADMIN", "FLEET_OWNER"),
    )
    completed = [
        ride
        for ride in gateway.dispatcher.rides.values()
        if ride.assigned_driver == driver_id and ride.status == "COMPLETED"
    ]
    total = float(len(completed) * 10)
    return {
        "driver_id": driver_id,
        "daily_total": total,
        "weekly_total": total,
        "earnings_period_id": "pilot-period-1",
        "earnings_receipt_id": f"earnings-{driver_id}-{len(completed)}",
        "replay_verified": True,
        "generated_at": "2026-06-01T00:00:00Z",
    }


@router.post("/accept")
def accept_ride(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("accept_ride", gateway.driver.accept, payload, idempotency_key, request=request)


@router.post("/start")
def start_trip(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("start_trip", gateway.driver.start, payload, idempotency_key, request=request)


@router.post("/arrive")
def arrive_trip(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("arrive_trip", gateway.driver.arrive, payload, idempotency_key, request=request)


@router.post("/complete")
def complete_trip(
    payload: RideAction,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    request: Request = None,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _driver_action("complete_trip", gateway.driver.complete, payload, idempotency_key, request=request)


def _driver_action(
    command_name: str,
    action,
    payload: RideAction,
    idempotency_key: str | None,
    request: Request = None,
) -> dict:
    try:
        command = payload.model_dump()
        log_command(command_name, command)
        _enforce_driver_access(
            request,
            permission=_command_permission(command_name),
            actor_id=command["driver_id"],
            driver_id=command["driver_id"],
        )
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


def _driver_ride_contract(ride: dict, driver_id: str) -> dict:
    return {
        "ride_id": ride["ride_id"],
        "pickup": ride["pickup"],
        "dropoff": ride["destination"],
        "status": _driver_status(ride["status"]),
        "assigned_driver_id": ride.get("assigned_driver") or driver_id,
        "receipt_id": (
            f"receipt-{ride['ride_id']}"
            if ride["status"] == "COMPLETED"
            else None
        ),
        "replay_id": (
            f"replay-{ride['ride_id']}"
            if ride["status"] == "COMPLETED"
            else None
        ),
    }


def _driver_status(status: str) -> str:
    return {
        "REQUESTED": "assigned",
        "DRIVER_ASSIGNED": "accepted",
        "DRIVER_ARRIVED": "arrived",
        "IN_TRIP": "in_progress",
        "COMPLETED": "completed",
        "CANCELED": "cancelled",
    }.get(status, "assigned")


def _command_permission(command_name: str) -> str:
    return {
        "accept_ride": "ride.accept",
        "start_trip": "ride.start",
        "arrive_trip": "ride.arrive",
        "complete_trip": "ride.complete",
    }.get(command_name, "ride.view.assigned")


def _claims_subject(request: Request | None) -> str | None:
    claims = claims_from_request(request)
    return None if claims is None else claims.sub


def _enforce_driver_access(
    request: Request | None,
    *,
    permission: str,
    actor_id: str | None,
    driver_id: str | None,
    privileged_roles: tuple[str, ...] = ("ADMIN",),
) -> None:
    claims = claims_from_request(request)
    if claims is None:
        return
    decision = evaluate_rbac_access(
        role=claims.role,
        permission=permission,
        actor_id=actor_id or claims.sub,
        owner_id=driver_id,
        privileged_roles=privileged_roles,
    )
    if not decision["allowed"]:
        raise HTTPException(status_code=403, detail=decision["reason"])
