"""AfriRide operational route glue for the top-level AfriTech API."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

_runtime = import_module("afriride_system.api.dependencies.runtime")
_driver_routes = import_module("afriride_system.api.driver_routes")
_idempotency = import_module("afriride_system.api.idempotency")
_passenger_routes = import_module("afriride_system.api.passenger_routes")
_schemas = import_module("afriride_system.api.schemas")
_dispatcher_adapter = import_module(
    "afriride_system.backend.command_api.command_dispatcher_adapter"
)

get_gateway = _runtime.get_gateway
arrive_trip = _driver_routes.arrive_trip
IdempotencyConflict = _idempotency.IdempotencyConflict
command_fingerprint = _idempotency.command_fingerprint
run_once = _idempotency.run_once
request_ride = _passenger_routes.request_ride
ride_status = _passenger_routes.ride_status
RequestRide = _schemas.RequestRide
RideAction = _schemas.RideAction
AfriRidePhase1Error = _dispatcher_adapter.AfriRidePhase1Error


def build_afriride_operational_router() -> APIRouter:
    router = APIRouter(tags=["afriride-operational"])

    @router.post("/ride/request")
    def ride_request_alias(
        payload: RequestRide,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        gateway: Any = Depends(get_gateway),
    ) -> dict:
        """Mobile-friendly alias for the passenger ride request contract."""

        return request_ride(payload, idempotency_key=idempotency_key, gateway=gateway)

    @router.get("/ride/{ride_id}/status")
    def ride_status_alias(
        ride_id: str,
        gateway: Any = Depends(get_gateway),
    ) -> dict:
        """Mobile-friendly alias for passenger ride status."""

        return ride_status(ride_id, gateway=gateway)

    @router.post("/ride/arrive")
    def ride_arrive_alias(
        payload: RideAction,
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        gateway: Any = Depends(get_gateway),
    ) -> dict:
        """Compatibility endpoint for driver apps that post ride_id in the body."""

        return arrive_trip(payload, idempotency_key=idempotency_key, gateway=gateway)

    @router.get("/ride/{ride_id}/price-explanation")
    def ride_price_explanation(
        ride_id: str,
        gateway: Any = Depends(get_gateway),
    ) -> dict[str, Any]:
        """Read-only deterministic fare explanation for mobile receipt screens."""

        try:
            ride = gateway.dispatcher.ride_status(ride_id)
        except AfriRidePhase1Error as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        distance_units = max(1, len(str(ride["pickup"])) + len(str(ride["destination"])))
        fare_units = round(4.0 + (distance_units * 0.35), 2)
        explanation = {
            "base_fare": 4.0,
            "distance_units": distance_units,
            "distance_component": round(distance_units * 0.35, 2),
            "currency": "USD",
            "total": fare_units,
            "rule": "base_fare + deterministic_route_units * 0.35",
        }
        return {
            "ride_id": ride_id,
            "price_explanation": explanation,
            "source": "core_system",
            "authority": "read_only_deterministic_pricing_projection",
        }

    @router.post("/ride/{ride_id}/cancel")
    def cancel_ride_contract(
        ride_id: str,
        payload: dict[str, Any],
        idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
        gateway: Any = Depends(get_gateway),
    ) -> dict:
        """Passenger cancellation contract for mobile clients."""

        passenger_id = str(payload.get("passenger_id", "")).strip()
        if not passenger_id:
            raise HTTPException(status_code=400, detail="missing_passenger_id")
        command = {"passenger_id": passenger_id, "ride_id": ride_id}
        try:
            result = run_once(
                idempotency_key,
                lambda: gateway.passenger.cancel(command),
                fingerprint=command_fingerprint("cancel_ride_contract", command),
            )
        except IdempotencyConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except AfriRidePhase1Error as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"status": "success", "data": result, "error": None}

    return router
