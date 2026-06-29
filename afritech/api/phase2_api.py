"""NovaRide Phase 2 dispatch, driver, and external payment API."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.api.realtime.ride_bus import ride_hub
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase2 import (
    build_phase2_status,
    execute_bounded_autonomous_dispatch,
    complete_trip,
    dispatch_ride,
    driver_accept,
    driver_arrive,
    driver_location,
    driver_offline,
    driver_online,
    driver_reject,
    request_and_dispatch_ride,
    start_trip,
)


class Phase2RideRequestBody(BaseModel):
    pickup: dict[str, Any]
    destination: dict[str, Any]
    fare_estimate: Decimal = Field(..., gt=0)
    currency: str = "AUD"
    driver_id: str | None = None
    payment_provider: str | None = None


class Phase2RideCompleteBody(BaseModel):
    final_fare: Decimal = Field(..., gt=0)
    driver_id: str | None = None


class Phase2AutonomousDispatchBody(BaseModel):
    payment_provider: str | None = None


class Phase2DriverLocationBody(BaseModel):
    location: dict[str, Any]
    trust_score: float | None = None


class Phase2DriverOnlineBody(BaseModel):
    location: dict[str, Any]
    trust_score: float | None = None


def _require_same_organization(requested_organization_id: str | None, claims: JWTClaims) -> str:
    org_id = requested_organization_id or claims.organization_id
    if org_id != claims.organization_id:
        raise HTTPException(status_code=403, detail="organization_isolation_violation")
    return org_id


def _require_active_subscription(organization_id: str) -> None:
    subscription = phase0_control_plane._STORE.latest_active_subscription(organization_id=organization_id)
    if subscription is None:
        raise HTTPException(status_code=403, detail="active_subscription_required")


def _ride_projection_payload(ride: dict[str, Any]) -> dict[str, Any]:
    return {
        "ride_id": ride["ride_id"],
        "status": ride["status"],
        "driver_id": ride.get("driver_id"),
        "passenger_id": ride.get("passenger_id"),
        "organization_id": ride.get("organization_id"),
        "pickup_location": ride.get("pickup_location"),
        "destination_location": ride.get("destination_location"),
        "fare_estimate": ride.get("fare_estimate"),
        "final_fare": ride.get("final_fare"),
        "currency": ride.get("currency"),
        "updated_at": ride.get("updated_at"),
    }


def build_phase2_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase2"])

    @router.get("/v1/novaride/phase2/status")
    def phase2_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase2_status(organization_id=org_id, limit=limit)

    @router.get("/v1/novaride/phase2/drivers")
    def phase2_drivers(
        status: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR", "ADMIN", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return {
            "view": "novaride_phase2_drivers",
            "organization_id": org_id,
            "drivers": phase0_control_plane._STORE.list_driver_presence(
                organization_id=org_id,
                status=status,
                limit=limit,
            ),
            "read_only": True,
        }

    @router.post("/v1/novaride/phase2/drivers/online")
    def phase2_driver_online(
        body: Phase2DriverOnlineBody,
        claims: JWTClaims = Depends(require_roles("DRIVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        result = driver_online(
            organization_id=org_id,
            driver_id=claims.sub,
            location=body.location,
            trust_score=body.trust_score or 0.0,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        return {"view": "novaride_phase2_driver_online", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/drivers/offline")
    def phase2_driver_offline(
        claims: JWTClaims = Depends(require_roles("DRIVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        result = driver_offline(
            organization_id=org_id,
            driver_id=claims.sub,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        return {"view": "novaride_phase2_driver_offline", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/drivers/location")
    def phase2_driver_location(
        body: Phase2DriverLocationBody,
        claims: JWTClaims = Depends(require_roles("DRIVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        result = driver_location(
            organization_id=org_id,
            driver_id=claims.sub,
            location=body.location,
            actor_user_id=claims.sub,
            actor_role=claims.role,
            trust_score=body.trust_score,
        )
        return {"view": "novaride_phase2_driver_location", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/rides/request")
    async def phase2_request_ride(
        body: Phase2RideRequestBody,
        claims: JWTClaims = Depends(require_roles("CUSTOMER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        result = request_and_dispatch_ride(
            organization_id=org_id,
            passenger_id=claims.sub,
            pickup=body.pickup,
            destination=body.destination,
            fare_estimate=body.fare_estimate,
            currency=body.currency,
            driver_id=body.driver_id,
            payment_provider=body.payment_provider,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        ride = result["dispatch"]["ride"] if result.get("dispatch") else result["ride_request"]["ride"]
        await ride_hub.publish_state_update(ride["ride_id"], _ride_projection_payload(ride))
        return {
            "view": "novaride_phase2_request_ride",
            "organization_id": org_id,
            "ride_request": result["ride_request"],
            "dispatch": result["dispatch"],
            "ready_for_live": bool(result.get("dispatch")),
            "ride": ride,
            "read_only": False,
        }

    @router.post("/v1/novaride/phase2/rides/{ride_id}/autonomous-dispatch")
    async def phase2_autonomous_dispatch(
        ride_id: str,
        body: Phase2AutonomousDispatchBody,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        result = execute_bounded_autonomous_dispatch(
            organization_id=org_id,
            ride_id=ride_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
            payment_provider=body.payment_provider,
        )
        if result.get("dispatch") and result["dispatch"].get("ride"):
            await ride_hub.publish_state_update(ride_id, _ride_projection_payload(result["dispatch"]["ride"]))
        return {
            "view": "novaride_phase2_autonomous_dispatch",
            "organization_id": org_id,
            **result,
            "read_only": False,
        }

    @router.post("/v1/novaride/phase2/rides/{ride_id}/dispatch")
    async def phase2_dispatch_ride(
        ride_id: str,
        body: dict[str, Any],
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.get("organization_id"), claims)
        _require_active_subscription(org_id)
        result = dispatch_ride(
            organization_id=org_id,
            ride_id=ride_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
            payment_provider=body.get("payment_provider"),
        )
        if result and result.get("ride"):
            await ride_hub.publish_state_update(ride_id, _ride_projection_payload(result["ride"]))
        return {"view": "novaride_phase2_dispatch", "organization_id": org_id, "dispatch": result, "read_only": False}

    @router.post("/v1/novaride/phase2/rides/{ride_id}/accept")
    async def phase2_driver_accept(
        ride_id: str,
        body: dict[str, Any],
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.get("organization_id"), claims)
        _require_active_subscription(org_id)
        driver_id = str(body.get("driver_id") or claims.sub)
        if claims.role == "DRIVER" and driver_id != claims.sub:
            raise HTTPException(status_code=403, detail="driver_identity_mismatch")
        result = driver_accept(
            organization_id=org_id,
            ride_id=ride_id,
            driver_id=driver_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        await ride_hub.publish_state_update(ride_id, _ride_projection_payload(result["ride"]))
        return {"view": "novaride_phase2_driver_accept", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/rides/{ride_id}/reject")
    async def phase2_driver_reject(
        ride_id: str,
        body: dict[str, Any],
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.get("organization_id"), claims)
        _require_active_subscription(org_id)
        driver_id = str(body.get("driver_id") or claims.sub)
        if claims.role == "DRIVER" and driver_id != claims.sub:
            raise HTTPException(status_code=403, detail="driver_identity_mismatch")
        result = driver_reject(
            organization_id=org_id,
            ride_id=ride_id,
            driver_id=driver_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        await ride_hub.publish_state_update(ride_id, _ride_projection_payload(result["ride"]))
        return {"view": "novaride_phase2_driver_reject", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/rides/{ride_id}/start")
    async def phase2_start_trip(
        ride_id: str,
        body: dict[str, Any],
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.get("organization_id"), claims)
        _require_active_subscription(org_id)
        driver_id = str(body.get("driver_id") or claims.sub)
        if claims.role == "DRIVER" and driver_id != claims.sub:
            raise HTTPException(status_code=403, detail="driver_identity_mismatch")
        result = start_trip(
            organization_id=org_id,
            ride_id=ride_id,
            driver_id=driver_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        ride = phase0_control_plane._STORE.get_ride(ride_id=ride_id, organization_id=org_id)
        if ride is not None:
            await ride_hub.publish_state_update(ride_id, _ride_projection_payload(ride))
        return {"view": "novaride_phase2_start_trip", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/rides/{ride_id}/arrive")
    async def phase2_arrive_trip(
        ride_id: str,
        body: dict[str, Any],
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.get("organization_id"), claims)
        _require_active_subscription(org_id)
        driver_id = str(body.get("driver_id") or claims.sub)
        if claims.role == "DRIVER" and driver_id != claims.sub:
            raise HTTPException(status_code=403, detail="driver_identity_mismatch")
        result = driver_arrive(
            organization_id=org_id,
            ride_id=ride_id,
            driver_id=driver_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        ride = phase0_control_plane._STORE.get_ride(ride_id=ride_id, organization_id=org_id)
        if ride is not None:
            await ride_hub.publish_state_update(ride_id, _ride_projection_payload(ride))
        return {"view": "novaride_phase2_arrive_trip", "organization_id": org_id, **result}

    @router.post("/v1/novaride/phase2/rides/{ride_id}/complete")
    async def phase2_complete_trip(
        ride_id: str,
        body: Phase2RideCompleteBody,
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        driver_id = body.driver_id or claims.sub
        if claims.role == "DRIVER" and driver_id != claims.sub:
            raise HTTPException(status_code=403, detail="driver_identity_mismatch")
        result = complete_trip(
            organization_id=org_id,
            ride_id=ride_id,
            driver_id=driver_id,
            final_fare=body.final_fare,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        ride = phase0_control_plane._STORE.get_ride(ride_id=ride_id, organization_id=org_id)
        if ride is not None:
            await ride_hub.publish_state_update(ride_id, _ride_projection_payload(ride))
        return {"view": "novaride_phase2_complete_trip", "organization_id": org_id, **result}

    @router.get("/v1/novaride/phase2/rides/{ride_id}")
    def phase2_ride_get(
        ride_id: str,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        ride = phase0_control_plane._STORE.get_ride(ride_id=ride_id, organization_id=org_id)
        if ride is None:
            raise HTTPException(status_code=404, detail="ride_not_found")
        return {"view": "novaride_phase2_ride", "organization_id": org_id, "ride": ride, "read_only": True}

    @router.get("/v1/novaride/phase2/rides")
    def phase2_rides(
        organization_id: str | None = None,
        passenger_id: str | None = None,
        driver_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return {
            "view": "novaride_phase2_rides",
            "organization_id": org_id,
            "rides": phase0_control_plane._STORE.list_rides(
                organization_id=org_id,
                passenger_id=passenger_id,
                driver_id=driver_id,
                status=status,
                limit=limit,
            ),
            "read_only": True,
        }

    @router.get("/v1/novaride/phase2/payments")
    def phase2_payments(
        organization_id: str | None = None,
        ride_id: str | None = None,
        provider: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return {
            "view": "novaride_phase2_payments",
            "organization_id": org_id,
            "authorizations": phase0_control_plane._STORE.list_external_payment_authorizations(
                organization_id=org_id,
                ride_id=ride_id,
                provider=provider,
                limit=limit,
            ),
            "captures": phase0_control_plane._STORE.list_external_payment_captures(
                organization_id=org_id,
                ride_id=ride_id,
                provider=provider,
                limit=limit,
            ),
            "read_only": True,
        }

    return router


__all__ = ["build_phase2_router"]
