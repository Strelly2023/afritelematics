"""NovaRide Phase 1 ride lifecycle, wallet, transaction, and event spine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_audit_log, build_control_projection, get_phase_store, phase_now


PHASE1_TOPIC = "novaride.phase1.ride_lifecycle"


@dataclass(frozen=True)
class Phase1RideRequest:
    organization_id: str
    passenger_id: str
    pickup: dict[str, Any]
    destination: dict[str, Any]
    fare_estimate: Decimal
    currency: str = "AUD"
    driver_id: str | None = None


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01")), ".2f")


def _store():
    return get_phase_store()


def publish_phase1_event(
    *,
    organization_id: str,
    event_type: str,
    ride_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return _store().publish_stream_event(
        organization_id=organization_id,
        topic_name=PHASE1_TOPIC,
        event_type=event_type,
        partition_key=ride_id,
        payload=payload,
    )


def create_wallet(
    *,
    organization_id: str,
    user_id: str,
    currency: str = "AUD",
    balance: Decimal | int | str = "0.00",
) -> dict[str, Any]:
    return _store().ensure_wallet(
        organization_id=organization_id,
        user_id=user_id,
        currency=currency,
        balance=balance,
    )


def credit_wallet(
    *,
    organization_id: str,
    user_id: str,
    currency: str,
    amount: Decimal | int | str,
    actor_user_id: str = "system",
    actor_role: str = "system",
) -> dict[str, Any]:
    wallet = _store().credit_wallet(
        organization_id=organization_id,
        user_id=user_id,
        currency=currency,
        amount=amount,
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase1.wallet_credit",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=user_id,
        status="recorded",
        payload={"currency": currency, "amount": _money_text(amount), "wallet": wallet},
    )
    return wallet


def list_wallets(
    *,
    organization_id: str | None = None,
    user_id: str | None = None,
    currency: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return _store().list_wallets(
        organization_id=organization_id,
        user_id=user_id,
        currency=currency,
        limit=limit,
    )


def request_ride(
    *,
    organization_id: str,
    passenger_id: str,
    pickup: dict[str, Any],
    destination: dict[str, Any],
    fare_estimate: Decimal | int | str,
    currency: str = "AUD",
    driver_id: str | None = None,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride_id = f"ride-{uuid4().hex[:12]}"
    ride = _store().store_ride(
        ride_id=ride_id,
        organization_id=organization_id,
        passenger_id=passenger_id,
        pickup_location=pickup,
        destination_location=destination,
        fare_estimate=fare_estimate,
        currency=currency,
        driver_id=driver_id,
        status="requested",
    )
    event = publish_phase1_event(
        organization_id=organization_id,
        event_type="ride_requested",
        ride_id=ride_id,
        payload=ride,
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase1.ride_requested",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"ride": ride, "event": event},
    )
    return {"ride": ride, "event": event}


def start_trip(
    *,
    organization_id: str,
    ride_id: str,
    driver_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = _store().update_ride(
        ride_id=ride_id,
        organization_id=organization_id,
        status="in_progress",
        driver_id=driver_id,
    )
    if ride is None:
        raise ValueError("ride not found")
    event = publish_phase1_event(
        organization_id=organization_id,
        event_type="trip_started",
        ride_id=ride_id,
        payload=ride,
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase1.trip_started",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"ride": ride, "event": event},
    )
    return {"ride": ride, "event": event}


def _process_payment(
    *,
    organization_id: str,
    ride: dict[str, Any],
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    if not ride.get("driver_id"):
        raise ValueError("driver_id required for payment")
    amount = Decimal(str(ride["final_fare"] or ride["fare_estimate"]))
    currency = str(ride["currency"])
    passenger_wallet = _store().debit_wallet(
        organization_id=organization_id,
        user_id=str(ride["passenger_id"]),
        currency=currency,
        amount=amount,
    )
    driver_wallet = _store().credit_wallet(
        organization_id=organization_id,
        user_id=str(ride["driver_id"]),
        currency=currency,
        amount=amount,
    )
    debit_txn = _store().store_transaction(
        organization_id=organization_id,
        ride_id=ride["ride_id"],
        user_id=str(ride["passenger_id"]),
        counterparty_user_id=str(ride["driver_id"]),
        amount=amount,
        currency=currency,
        transaction_type="debit",
        status="completed",
    )
    credit_txn = _store().store_transaction(
        organization_id=organization_id,
        ride_id=ride["ride_id"],
        user_id=str(ride["driver_id"]),
        counterparty_user_id=str(ride["passenger_id"]),
        amount=amount,
        currency=currency,
        transaction_type="credit",
        status="completed",
    )
    payment_event = publish_phase1_event(
        organization_id=organization_id,
        event_type="payment_processed",
        ride_id=ride["ride_id"],
        payload={
            "ride_id": ride["ride_id"],
            "passenger_wallet": passenger_wallet,
            "driver_wallet": driver_wallet,
            "transactions": [debit_txn, credit_txn],
        },
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase1.payment_processed",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride["ride_id"],
        status="recorded",
        payload={
            "passenger_wallet": passenger_wallet,
            "driver_wallet": driver_wallet,
            "transactions": [debit_txn, credit_txn],
            "event": payment_event,
        },
    )
    return {
        "passenger_wallet": passenger_wallet,
        "driver_wallet": driver_wallet,
        "transactions": [debit_txn, credit_txn],
        "event": payment_event,
    }


def complete_trip(
    *,
    organization_id: str,
    ride_id: str,
    final_fare: Decimal | int | str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = _store().update_ride(
        ride_id=ride_id,
        organization_id=organization_id,
        status="completed",
        final_fare=final_fare,
        completed_at=_now(),
    )
    if ride is None:
        raise ValueError("ride not found")
    ride_event = publish_phase1_event(
        organization_id=organization_id,
        event_type="trip_completed",
        ride_id=ride_id,
        payload=ride,
    )
    payment = _process_payment(
        organization_id=organization_id,
        ride=ride,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase1.trip_completed",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"ride": ride, "ride_event": ride_event, "payment": payment},
    )
    return {"ride": ride, "ride_event": ride_event, "payment": payment}


def get_ride(*, organization_id: str, ride_id: str) -> dict[str, Any] | None:
    return _store().get_ride(ride_id=ride_id, organization_id=organization_id)


def list_rides(
    *,
    organization_id: str | None = None,
    passenger_id: str | None = None,
    driver_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return _store().list_rides(
        organization_id=organization_id,
        passenger_id=passenger_id,
        driver_id=driver_id,
        status=status,
        limit=limit,
    )


def list_transactions(
    *,
    organization_id: str | None = None,
    ride_id: str | None = None,
    user_id: str | None = None,
    transaction_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return _store().list_transactions(
        organization_id=organization_id,
        ride_id=ride_id,
        user_id=user_id,
        transaction_type=transaction_type,
        limit=limit,
    )


def list_events(
    *,
    organization_id: str | None = None,
    after_offset: int = 0,
    limit: int = 100,
) -> list[dict[str, Any]]:
    return _store().list_stream_events(
        organization_id=organization_id,
        topic_name=PHASE1_TOPIC,
        after_offset=after_offset,
        limit=limit,
    )


def build_phase1_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    rides = list_rides(organization_id=org_id, limit=limit)
    wallets = list_wallets(organization_id=org_id, limit=limit)
    transactions = list_transactions(organization_id=org_id, limit=limit)
    events = list_events(organization_id=org_id, limit=limit)
    audit_log = build_audit_log(organization_id=org_id)
    completed_rides = [ride for ride in rides if ride["status"] == "completed"]
    payment_events = [event for event in events if event["event_type"] == "payment_processed"]
    readiness = {
        "ride_lifecycle_runs": any(ride["status"] == "completed" for ride in rides),
        "events_stored": len(events) >= 3,
        "wallet_updates": len(wallets) >= 2,
        "transactions_recorded": len(transactions) >= 2,
        "payments_automated": len(payment_events) >= 1 and len(transactions) >= 2,
        "all_actions_audited": audit_log["count"] >= 4,
        "tenant_isolation_preserved": all(
            item["organization_id"] == org_id for item in rides + wallets + transactions + events
        ),
    }
    return {
        "view": "novaride_phase1_status",
        "phase": "1",
        "platform": "NovaRide Phase 1",
        "organization_id": org_id,
        "topic": PHASE1_TOPIC,
        "rides": rides,
        "wallets": wallets,
        "transactions": transactions,
        "events": events,
        "completed_rides": completed_rides,
        "audit_log": audit_log,
        "readiness": readiness,
        "ready": all(readiness.values()),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE1_TOPIC",
    "Phase1RideRequest",
    "build_phase1_status",
    "complete_trip",
    "create_wallet",
    "credit_wallet",
    "get_ride",
    "list_events",
    "list_rides",
    "list_transactions",
    "list_wallets",
    "publish_phase1_event",
    "request_ride",
    "start_trip",
]
