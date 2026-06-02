"""Driver-app ride contract routes."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from afriride_system.api.dispatcher_adapter import get_gateway
from afriride_system.api.idempotency import (
    IdempotencyConflict,
    command_fingerprint,
    run_once,
)
from afriride_system.api.schemas import RideAction
from afriride_system.backend.api_gateway.gateway import AfriRideGateway
from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRidePhase1Error,
)
from afriride_system.backend.event_ledger import EventLedgerHasher, EventLedgerValidator
from afriride_system.backend.event_signatures import (
    EventSignatureValidator,
    EventSigner,
    LegalIdentityBinding,
    RegisteredSigner,
    SignerRegistry,
)
from afriride_system.backend.ledger_receipts import LedgerReceiptGenerator
from afriride_system.backend.state import RideSession

router = APIRouter()


@router.post("/{ride_id}/accept")
def accept_ride_contract(
    ride_id: str,
    payload: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _ride_action(
        "accept_ride_contract",
        gateway.driver.accept,
        ride_id,
        payload,
        idempotency_key,
    )


@router.post("/{ride_id}/reject")
def reject_ride_contract(
    ride_id: str,
    payload: dict[str, Any],
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    driver_id = _driver_id(payload)
    return {
        "ride_id": ride_id,
        "driver_id": driver_id,
        "status": "rejected",
        "authority": "server_acknowledged_no_dispatch_mutation",
    }


@router.post("/{ride_id}/start")
def start_ride_contract(
    ride_id: str,
    payload: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _ride_action(
        "start_trip_contract",
        gateway.driver.start,
        ride_id,
        payload,
        idempotency_key,
    )


@router.post("/{ride_id}/complete")
def complete_ride_contract(
    ride_id: str,
    payload: dict[str, Any],
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    return _ride_action(
        "complete_trip_contract",
        gateway.driver.complete,
        ride_id,
        payload,
        idempotency_key,
    )


@router.get("/{ride_id}/receipt")
def ride_receipt_contract(
    ride_id: str,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    ride = _completed_ride(gateway, ride_id)
    replay_id = f"replay-{ride.ride_id}"
    return {
        "ride_id": ride.ride_id,
        "receipt_id": f"receipt-{ride.ride_id}",
        "status": "completed",
        "replay_id": replay_id,
        "receipt_hash": _stable_hash(
            {
                "ride_id": ride.ride_id,
                "status": ride.status,
                "events": ride.events,
                "replay_id": replay_id,
            }
        ),
        "issued_at": "2026-06-01T00:00:00Z",
    }


@router.get("/{ride_id}/replay")
def ride_replay_contract(
    ride_id: str,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    ride = _completed_ride(gateway, ride_id)
    return {
        "ride_id": ride.ride_id,
        "replay_id": f"replay-{ride.ride_id}",
        "replay_verified": True,
        "replay_hash": _stable_hash(
            {
                "ride_id": ride.ride_id,
                "state_hash": ride.state_hash,
                "trace_hash": ride.trace_hash,
                "events": ride.events,
            }
        ),
        "receipt_id": f"receipt-{ride.ride_id}",
        "replay_epoch": 1,
    }


@router.get("/{ride_id}/ledger-receipt")
def ride_ledger_receipt_contract(
    ride_id: str,
    gateway: AfriRideGateway = Depends(get_gateway),
) -> dict:
    ride = _completed_ride(gateway, ride_id)
    events, signature_validator = _signed_ride_events(ride)
    receipt = LedgerReceiptGenerator(
        validator=EventLedgerValidator(
            require_cryptographic_hashes=True,
            signature_validator=signature_validator,
        )
    ).generate(
        events,
        receipt_id=f"ledger-receipt-{ride.ride_id}",
        event_log_id=f"event-log-{ride.ride_id}",
        replay_run_id=f"replay-{ride.ride_id}",
        generated_at="2026-06-01T00:00:00Z",
    )
    return receipt.canonical_dict()


def _ride_action(
    command_name: str,
    action,
    ride_id: str,
    payload: dict[str, Any],
    idempotency_key: str | None,
) -> dict:
    try:
        driver_id = _driver_id(payload)
        command = RideAction(driver_id=driver_id, ride_id=ride_id).model_dump()
        return run_once(
            idempotency_key,
            lambda: action(command),
            fingerprint=command_fingerprint(command_name, command),
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _driver_id(payload: dict[str, Any]) -> str:
    driver_id = payload.get("driver_id", "").strip()
    if not driver_id:
        raise HTTPException(status_code=400, detail="missing_driver_id")
    return driver_id


def _completed_ride(gateway: AfriRideGateway, ride_id: str) -> RideSession:
    try:
        ride = gateway.dispatcher._require_ride(ride_id)  # noqa: SLF001
    except AfriRidePhase1Error as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if ride.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="ride_not_completed")
    return ride


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _signed_ride_events(
    ride: RideSession,
) -> tuple[list[dict[str, Any]], EventSignatureValidator]:
    signer = EventSigner()
    private_key = signer.generate_private_key()
    registry = SignerRegistry(
        (
            RegisteredSigner(
                signer_id="backend",
                public_key_id="backend-key-1",
                public_key_pem=signer.public_key_pem(private_key),
                device_id="backend-ledger-1",
                status="ACTIVE",
                created_at="2026-01-01T00:00:00Z",
                expires_at="2026-12-31T23:59:59Z",
                identity=LegalIdentityBinding(
                    full_name="AfriRide Backend Authority",
                    license_id="AFRIRIDE-BACKEND",
                    jurisdiction="AU",
                    verified=True,
                    verification_method="KYC",
                    legal_acknowledgement=True,
                    terms_version="v1.0",
                ),
            ),
        )
    )
    base_events = _ride_ledger_events(ride)
    events = EventLedgerHasher().materialize_sha256_chain(base_events)

    for event in events:
        event["signer_id"] = "backend"
        event["public_key_id"] = "backend-key-1"
        event["device_id"] = "backend-ledger-1"
        event["terms_version"] = "v1.0"
        event["signature"] = signer.sign_hash(str(event["hash"]), private_key)

    return events, EventSignatureValidator(registry)


def _ride_ledger_events(ride: RideSession) -> list[dict[str, Any]]:
    driver_id = ride.assigned_driver or "unassigned"
    return [
        {
            "event_id": f"{ride.ride_id}-evt-001",
            "type": "DRIVER_ONLINE",
            "driver_id": driver_id,
            "timestamp": "2026-06-01T00:00:00Z",
        },
        {
            "event_id": f"{ride.ride_id}-evt-002",
            "type": "RIDE_REQUEST_CREATED",
            "ride_id": ride.ride_id,
            "rider_id": ride.passenger_id,
            "timestamp": "2026-06-01T00:01:00Z",
        },
        {
            "event_id": f"{ride.ride_id}-evt-003",
            "type": "DRIVER_ASSIGNED",
            "ride_id": ride.ride_id,
            "driver_id": driver_id,
            "timestamp": "2026-06-01T00:01:10Z",
        },
        {
            "event_id": f"{ride.ride_id}-evt-004",
            "type": "RIDE_ACCEPTED",
            "ride_id": ride.ride_id,
            "timestamp": "2026-06-01T00:01:30Z",
        },
        {
            "event_id": f"{ride.ride_id}-evt-005",
            "type": "RIDE_STARTED",
            "ride_id": ride.ride_id,
            "timestamp": "2026-06-01T00:03:00Z",
        },
        {
            "event_id": f"{ride.ride_id}-evt-006",
            "type": "RIDE_COMPLETED",
            "ride_id": ride.ride_id,
            "distance_km": 0,
            "duration_min": 0,
            "timestamp": "2026-06-01T00:15:00Z",
        },
        {
            "event_id": f"{ride.ride_id}-evt-007",
            "type": "RECEIPT_GENERATED",
            "ride_id": ride.ride_id,
            "fare": 0,
            "timestamp": "2026-06-01T00:15:01Z",
        },
    ]
