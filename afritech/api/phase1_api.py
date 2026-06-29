"""NovaRide Phase 1 ride lifecycle API."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from afritech.api.auth.jwt_device_auth import JWTClaims, require_roles
from afritech.afriprogramming import control_plane as phase0_control_plane
from afritech.afriprogramming.phase1 import (
    build_phase1_status,
    complete_trip,
    create_wallet,
    credit_wallet,
    get_ride,
    list_events,
    list_rides,
    list_transactions,
    list_wallets,
    request_ride,
    start_trip,
)


class Phase1RideRequestBody(BaseModel):
    pickup: dict[str, Any]
    destination: dict[str, Any]
    fare_estimate: Decimal = Field(..., gt=0)
    currency: str = "AUD"
    driver_id: str | None = None


class Phase1RideCompleteBody(BaseModel):
    final_fare: Decimal = Field(..., gt=0)


class Phase1WalletBody(BaseModel):
    user_id: str
    currency: str = "AUD"
    balance: Decimal = Field(default=Decimal("0.00"), ge=0)


class Phase1WalletCreditBody(BaseModel):
    user_id: str
    currency: str = "AUD"
    amount: Decimal = Field(..., gt=0)


def _require_same_organization(requested_organization_id: str | None, claims: JWTClaims) -> str:
    org_id = requested_organization_id or claims.organization_id
    if org_id != claims.organization_id:
        raise HTTPException(status_code=403, detail="organization_isolation_violation")
    return org_id


def _require_active_subscription(organization_id: str) -> None:
    subscription = phase0_control_plane._STORE.latest_active_subscription(organization_id=organization_id)
    if subscription is None:
        raise HTTPException(status_code=403, detail="active_subscription_required")


def build_phase1_router() -> APIRouter:
    router = APIRouter(tags=["novaride-phase1"])

    @router.get("/v1/novaride/phase1/status")
    def phase1_status(
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        return build_phase1_status(organization_id=org_id, limit=limit)

    @router.post("/v1/novaride/phase1/wallets")
    def phase1_wallet_create(
        body: Phase1WalletBody,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        wallet = create_wallet(
            organization_id=org_id,
            user_id=body.user_id,
            currency=body.currency,
            balance=body.balance,
        )
        return {"view": "novaride_phase1_wallet", "organization_id": org_id, "wallet": wallet, "read_only": False}

    @router.post("/v1/novaride/phase1/wallets/credit")
    def phase1_wallet_credit(
        body: Phase1WalletCreditBody,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        wallet = credit_wallet(
            organization_id=org_id,
            user_id=body.user_id,
            currency=body.currency,
            amount=body.amount,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )
        return {"view": "novaride_phase1_wallet_credit", "organization_id": org_id, "wallet": wallet, "read_only": False}

    @router.get("/v1/novaride/phase1/wallets")
    def phase1_wallets(
        organization_id: str | None = None,
        user_id: str | None = None,
        currency: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return {"view": "novaride_phase1_wallets", "organization_id": org_id, "wallets": list_wallets(organization_id=org_id, user_id=user_id, currency=currency, limit=limit), "read_only": True}

    @router.post("/v1/novaride/phase1/rides/request")
    def phase1_request_ride(
        body: Phase1RideRequestBody,
        claims: JWTClaims = Depends(require_roles("CUSTOMER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        return request_ride(
            organization_id=org_id,
            passenger_id=claims.sub,
            pickup=body.pickup,
            destination=body.destination,
            fare_estimate=body.fare_estimate,
            currency=body.currency,
            driver_id=body.driver_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/v1/novaride/phase1/rides/{ride_id}/start")
    def phase1_start_trip(
        ride_id: str,
        body: dict[str, Any],
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(body.get("organization_id"), claims)
        _require_active_subscription(org_id)
        driver_id = str(body.get("driver_id") or claims.sub)
        if claims.role == "DRIVER" and driver_id != claims.sub:
            raise HTTPException(status_code=403, detail="driver_identity_mismatch")
        return start_trip(
            organization_id=org_id,
            ride_id=ride_id,
            driver_id=driver_id,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.post("/v1/novaride/phase1/rides/{ride_id}/complete")
    def phase1_complete_trip(
        ride_id: str,
        body: Phase1RideCompleteBody,
        claims: JWTClaims = Depends(require_roles("DRIVER", "OPERATOR")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        _require_active_subscription(org_id)
        return complete_trip(
            organization_id=org_id,
            ride_id=ride_id,
            final_fare=body.final_fare,
            actor_user_id=claims.sub,
            actor_role=claims.role,
        )

    @router.get("/v1/novaride/phase1/rides/{ride_id}")
    def phase1_ride_get(
        ride_id: str,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(None, claims)
        ride = get_ride(organization_id=org_id, ride_id=ride_id)
        if ride is None:
            raise HTTPException(status_code=404, detail="ride_not_found")
        return {"view": "novaride_phase1_ride", "organization_id": org_id, "ride": ride, "read_only": True}

    @router.get("/v1/novaride/phase1/rides")
    def phase1_rides(
        organization_id: str | None = None,
        passenger_id: str | None = None,
        driver_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("CUSTOMER", "DRIVER", "OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return {"view": "novaride_phase1_rides", "organization_id": org_id, "rides": list_rides(organization_id=org_id, passenger_id=passenger_id, driver_id=driver_id, status=status, limit=limit), "read_only": True}

    @router.get("/v1/novaride/phase1/transactions")
    def phase1_transactions(
        organization_id: str | None = None,
        ride_id: str | None = None,
        user_id: str | None = None,
        transaction_type: str | None = None,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return {"view": "novaride_phase1_transactions", "organization_id": org_id, "transactions": list_transactions(organization_id=org_id, ride_id=ride_id, user_id=user_id, transaction_type=transaction_type, limit=limit), "read_only": True}

    @router.get("/v1/novaride/phase1/events")
    def phase1_events(
        organization_id: str | None = None,
        after_offset: int = 0,
        limit: int = 100,
        claims: JWTClaims = Depends(require_roles("OPERATOR", "ADMIN", "VERIFIER", "OBSERVER")),
    ) -> dict[str, Any]:
        org_id = _require_same_organization(organization_id, claims)
        return {"view": "novaride_phase1_events", "organization_id": org_id, "events": list_events(organization_id=org_id, after_offset=after_offset, limit=limit), "read_only": True}

    return router


__all__ = ["build_phase1_router"]
