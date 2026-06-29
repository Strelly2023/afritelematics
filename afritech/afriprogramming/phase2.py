"""NovaRide Phase 2 dispatch, driver presence, and external payment orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import os
from typing import Any

from afritech.afriprogramming.phase_common import DEFAULT_ORGANIZATION_ID, build_audit_log, build_control_projection, get_phase_store, phase_now
from uuid import uuid4

from afritech.afriprogramming.phase1 import (
    build_phase1_status,
    complete_trip as phase1_complete_trip,
    get_ride,
    request_ride as phase1_request_ride,
    start_trip as phase1_start_trip,
)
from afritech.core_platform.models import PaymentIntent
from afritech.core_platform.payments.providers import provider_for
from afritech.dispatch import dispatch_ride as assign_dispatch_ride
from afritech.dispatch import (
    get_driver_presence,
    list_driver_presence,
    release_driver,
    set_driver_offline,
    set_driver_online,
    update_driver_location,
)


PHASE2_TOPIC = "novaride.phase2.dispatch_driver_payment"


def _store():
    return get_phase_store()


def _now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _money_text(value: Decimal | int | str) -> str:
    return format(Decimal(str(value)).quantize(Decimal("0.01")), ".2f")


def _pickup_location(ride: dict[str, Any]) -> dict[str, Any]:
    return dict(ride.get("pickup_location") or {})


def _destination_location(ride: dict[str, Any]) -> dict[str, Any]:
    return dict(ride.get("destination_location") or {})


def _country_from_location(location: dict[str, Any]) -> str:
    country = str(location.get("country") or location.get("country_code") or "").strip().upper()
    if country:
        return country
    label = str(location.get("label") or location.get("name") or "").strip().upper()
    if label.startswith("AU"):
        return "AU"
    return ""


def _route_class(ride: dict[str, Any]) -> str:
    pickup_country = _country_from_location(_pickup_location(ride))
    destination_country = _country_from_location(_destination_location(ride))
    if pickup_country and destination_country and pickup_country != destination_country:
        return "cross_border"
    return "domestic"


def _default_payment_provider(ride: dict[str, Any]) -> str:
    currency = str(ride.get("currency") or "AUD").upper()
    if _route_class(ride) == "cross_border":
        return "mfs_africa"
    if currency in {"KES", "BIF", "CDF"}:
        return "mobile_money"
    # Australian NovaRide rehearsals use the controlled PayID implementation.
    # Live execution remains gated by NOVAPAY_PAYID_LIVE_ENABLED.
    return "payid"


def _payment_live_mode(provider: str) -> bool:
    normalized = provider.strip().lower()
    if normalized == "stripe":
        return os.environ.get("STRIPE_LIVE_MODE", "").lower() in {"1", "true", "yes"}
    if normalized in {"payid", "pay_id", "osko"}:
        return os.environ.get("NOVAPAY_PAYID_LIVE_ENABLED", "").lower() in {"1", "true", "yes"}
    if normalized == "mfs_africa":
        return os.environ.get("MFS_AFRICA_LIVE_MODE", "").lower() in {"1", "true", "yes"}
    if normalized in {"mobile_money", "mobile-money", "momo"}:
        return os.environ.get("NOVAPAY_MOBILE_MONEY_LIVE_ENABLED", "").lower() in {"1", "true", "yes"}
    return False


def publish_phase2_event(
    *,
    organization_id: str,
    event_type: str,
    ride_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return _store().publish_stream_event(
        organization_id=organization_id,
        topic_name=PHASE2_TOPIC,
        event_type=event_type,
        partition_key=ride_id,
        payload=payload,
    )


def dispatch_ride(
    *,
    organization_id: str,
    ride_id: str,
    actor_user_id: str,
    actor_role: str,
    excluded_driver_ids: set[str] | None = None,
    payment_provider: str | None = None,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    dispatch = assign_dispatch_ride(
        organization_id=organization_id,
        ride=ride,
        excluded_driver_ids=excluded_driver_ids,
    )
    if dispatch is None:
        event = publish_phase2_event(
            organization_id=organization_id,
            event_type="ride_dispatch_pending",
            ride_id=ride_id,
            payload={"ride": ride, "reason": "no_available_driver"},
        )
        _store().record_audit_event(
            organization_id=organization_id,
            event_type="phase2.ride_dispatch_pending",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=ride_id,
            status="recorded",
            payload={"ride": ride, "event": event},
        )
        return {"ride": ride, "dispatch": None, "payment_authorization": None, "event": event}

    authorized = authorize_external_payment(
        organization_id=organization_id,
        ride_id=ride_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        provider=payment_provider,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="ride_dispatched",
        ride_id=ride_id,
        payload={"ride": dispatch["ride"], "dispatch": dispatch, "payment_authorization": authorized},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.ride_dispatched",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"dispatch": dispatch, "payment_authorization": authorized, "event": event},
    )
    return {
        "ride": dispatch["ride"],
        "dispatch": dispatch,
        "payment_authorization": authorized,
        "event": event,
    }


def driver_online(
    *,
    organization_id: str,
    driver_id: str,
    location: dict[str, Any],
    actor_user_id: str,
    actor_role: str,
    trust_score: float = 0.0,
) -> dict[str, Any]:
    presence = set_driver_online(
        organization_id=organization_id,
        driver_id=driver_id,
        location=location,
        trust_score=trust_score,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="driver_online",
        ride_id=driver_id,
        payload={"presence": presence},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.driver_online",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=driver_id,
        status="recorded",
        payload={"presence": presence, "event": event},
    )
    return {"presence": presence, "event": event}


def driver_offline(
    *,
    organization_id: str,
    driver_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    presence = set_driver_offline(
        organization_id=organization_id,
        driver_id=driver_id,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="driver_offline",
        ride_id=driver_id,
        payload={"presence": presence},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.driver_offline",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=driver_id,
        status="recorded",
        payload={"presence": presence, "event": event},
    )
    return {"presence": presence, "event": event}


def driver_location(
    *,
    organization_id: str,
    driver_id: str,
    location: dict[str, Any],
    actor_user_id: str,
    actor_role: str,
    trust_score: float | None = None,
) -> dict[str, Any]:
    presence = update_driver_location(
        organization_id=organization_id,
        driver_id=driver_id,
        location=location,
        trust_score=trust_score,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="driver_location_updated",
        ride_id=driver_id,
        payload={"presence": presence},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.driver_location_updated",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=driver_id,
        status="recorded",
        payload={"presence": presence, "event": event},
    )
    return {"presence": presence, "event": event}


def driver_accept(
    *,
    organization_id: str,
    ride_id: str,
    driver_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    if ride.get("driver_id") and ride["driver_id"] != driver_id:
        raise ValueError("driver_mismatch")
    dispatch = _store().store_dispatch_assignment(
        organization_id=organization_id,
        ride_id=ride_id,
        driver_id=driver_id,
        status="accepted",
        decision={"driver_id": driver_id, "accepted_at": _now()},
    )
    ride = _store().update_ride(
        ride_id=ride_id,
        organization_id=organization_id,
        status="matched",
        driver_id=driver_id,
    )
    current_presence = get_driver_presence(organization_id=organization_id, driver_id=driver_id) or {}
    presence = _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=driver_id,
        status="busy",
        location=current_presence.get("location", {}),
        busy_ride_id=ride_id,
        trust_score=float(current_presence.get("trust_score", 0.0)),
        metadata={"accepted_ride_id": ride_id},
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="driver_accepted",
        ride_id=ride_id,
        payload={"ride": ride, "assignment": dispatch, "presence": presence},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.driver_accepted",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"ride": ride, "assignment": dispatch, "presence": presence, "event": event},
    )
    return {"ride": ride, "assignment": dispatch, "presence": presence, "event": event}


def driver_arrive(
    *,
    organization_id: str,
    ride_id: str,
    driver_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    if ride.get("driver_id") and ride["driver_id"] != driver_id:
        raise ValueError("driver_mismatch")
    if ride.get("status") not in {"matched", "arriving"}:
        raise ValueError("ride_not_ready_for_arrival")
    ride = _store().update_ride(
        ride_id=ride_id,
        organization_id=organization_id,
        status="arrived",
        driver_id=driver_id,
    )
    if ride is None:
        raise ValueError("ride not found")
    current_presence = get_driver_presence(organization_id=organization_id, driver_id=driver_id) or {}
    presence = _store().store_driver_presence(
        organization_id=organization_id,
        driver_id=driver_id,
        status="busy",
        location=current_presence.get("location", {}),
        busy_ride_id=ride_id,
        trust_score=float(current_presence.get("trust_score", 0.0)),
        metadata={"arrived_ride_id": ride_id},
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="driver_arrived",
        ride_id=ride_id,
        payload={"ride": ride, "presence": presence},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.driver_arrived",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"ride": ride, "presence": presence, "event": event},
    )
    return {"ride": ride, "presence": presence, "event": event}


def driver_reject(
    *,
    organization_id: str,
    ride_id: str,
    driver_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    current_driver = ride.get("driver_id")
    if current_driver and current_driver != driver_id:
        raise ValueError("driver_mismatch")
    release_driver(
        organization_id=organization_id,
        driver_id=driver_id,
        status="online",
        busy_ride_id=None,
    )
    ride = _store().update_ride(
        ride_id=ride_id,
        organization_id=organization_id,
        status="requested",
        driver_id=None,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="driver_rejected",
        ride_id=ride_id,
        payload={"ride": ride, "driver_id": driver_id},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.driver_rejected",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"ride": ride, "driver_id": driver_id, "event": event},
    )
    rematch = dispatch_ride(
        organization_id=organization_id,
        ride_id=ride_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        excluded_driver_ids={driver_id},
    )
    return {"ride": ride, "event": event, "rematch": rematch}


def start_trip(
    *,
    organization_id: str,
    ride_id: str,
    driver_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    if ride.get("driver_id") and ride["driver_id"] != driver_id:
        raise ValueError("driver_mismatch")
    if ride.get("status") != "arrived":
        raise ValueError("ride_not_ready_for_start")
    payload = phase1_start_trip(
        organization_id=organization_id,
        ride_id=ride_id,
        driver_id=driver_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="trip_started",
        ride_id=ride_id,
        payload=payload,
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.trip_started",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"payload": payload, "event": event},
    )
    return {"payload": payload, "event": event}


def authorize_external_payment(
    *,
    organization_id: str,
    ride_id: str,
    actor_user_id: str,
    actor_role: str,
    provider: str | None = None,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    selected_provider = provider or _default_payment_provider(ride)
    active_subscription = _store().latest_active_subscription(organization_id=organization_id)
    intent = PaymentIntent(
        intent_id=f"intent-{ride_id}",
        actor_id=str(ride["passenger_id"]),
        organization_id=organization_id,
        amount=Decimal(str(ride.get("fare_estimate") or "0.00")),
        currency=str(ride.get("currency") or "AUD"),
        destination=f"ride:{ride_id}",
        metadata={
            "ride_id": ride_id,
            "driver_id": ride.get("driver_id"),
            "route_class": _route_class(ride),
            "payment_provider": selected_provider,
            "commercial_approval_reference": str(
                (active_subscription or {}).get("plan")
                or os.environ.get("MFS_AFRICA_COMMERCIAL_APPROVAL_REFERENCE", "")
                or "phase2-pilot"
            ),
        },
    )
    provider_adapter = provider_for(selected_provider, live=_payment_live_mode(selected_provider), intent=intent)
    provider_result = provider_adapter.authorize(intent)
    auth = _store().store_external_payment_authorization(
        organization_id=organization_id,
        ride_id=ride_id,
        provider=provider_result.provider,
        provider_reference=provider_result.provider_reference,
        amount=ride.get("fare_estimate") or "0.00",
        currency=str(ride.get("currency") or "AUD"),
        status=provider_result.status,
        settlement_status=provider_result.settlement_status,
        capture_status="pending_capture",
        raw={
            "request": intent.canonical(),
            "provider_result": provider_result.raw,
        },
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="payment_authorized",
        ride_id=ride_id,
        payload={"authorization": auth, "provider_result": provider_result.raw},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.payment_authorized",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"authorization": auth, "provider_result": provider_result.raw, "event": event},
    )
    return {"authorization": auth, "provider_result": provider_result.raw, "event": event}


def capture_external_payment(
    *,
    organization_id: str,
    ride_id: str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    auth = _store().get_external_payment_authorization(organization_id=organization_id, ride_id=ride_id)
    if auth is None:
        raise ValueError("payment authorization not found")
    capture = _store().store_external_payment_capture(
        organization_id=organization_id,
        ride_id=ride_id,
        authorization_id=auth["authorization_id"],
        provider=auth["provider"],
        provider_reference=auth["provider_reference"],
        amount=auth["amount"],
        currency=auth["currency"],
        status="captured",
        raw={
            "authorization": auth,
            "captured_at": _now(),
        },
    )
    updated_auth = _store().store_external_payment_authorization(
        organization_id=organization_id,
        ride_id=ride_id,
        provider=auth["provider"],
        provider_reference=auth["provider_reference"],
        amount=auth["amount"],
        currency=auth["currency"],
        status=auth["status"],
        settlement_status=auth["settlement_status"],
        capture_status="captured",
        raw=auth["raw"],
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="payment_captured",
        ride_id=ride_id,
        payload={"capture": capture, "authorization": updated_auth},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.payment_captured",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"capture": capture, "authorization": updated_auth, "event": event},
    )
    return {"capture": capture, "authorization": updated_auth, "event": event}


def complete_trip(
    *,
    organization_id: str,
    ride_id: str,
    driver_id: str,
    final_fare: Decimal | int | str,
    actor_user_id: str,
    actor_role: str,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    if ride.get("driver_id") and ride["driver_id"] != driver_id:
        raise ValueError("driver_mismatch")
    if ride.get("status") != "in_progress":
        raise ValueError("ride_not_ready_for_completion")
    trip = phase1_complete_trip(
        organization_id=organization_id,
        ride_id=ride_id,
        final_fare=final_fare,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )
    payment = capture_external_payment(
        organization_id=organization_id,
        ride_id=ride_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )
    ride = trip["ride"]
    if ride.get("driver_id"):
        release_driver(
            organization_id=organization_id,
            driver_id=str(ride["driver_id"]),
            status="online",
            busy_ride_id=None,
        )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="trip_completed",
        ride_id=ride_id,
        payload={"trip": trip, "payment": payment},
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.trip_completed",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={"trip": trip, "payment": payment, "event": event},
    )
    return {"trip": trip, "payment": payment, "event": event}


def request_and_dispatch_ride(
    *,
    organization_id: str,
    passenger_id: str,
    pickup: dict[str, Any],
    destination: dict[str, Any],
    fare_estimate: Decimal | int | str,
    currency: str,
    actor_user_id: str,
    actor_role: str,
    driver_id: str | None = None,
    payment_provider: str | None = None,
) -> dict[str, Any]:
    ride_request = phase1_request_ride(
        organization_id=organization_id,
        passenger_id=passenger_id,
        pickup=pickup,
        destination=destination,
        fare_estimate=fare_estimate,
        currency=currency,
        driver_id=driver_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
    )
    ride = ride_request["ride"]
    dispatch = dispatch_ride(
        organization_id=organization_id,
        ride_id=ride["ride_id"],
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        payment_provider=payment_provider,
    )
    return {"ride_request": ride_request, "dispatch": dispatch}


def execute_bounded_autonomous_dispatch(
    *,
    organization_id: str,
    ride_id: str,
    actor_user_id: str,
    actor_role: str,
    payment_provider: str | None = None,
) -> dict[str, Any]:
    ride = get_ride(organization_id=organization_id, ride_id=ride_id)
    if ride is None:
        raise ValueError("ride not found")
    autonomy_surface = build_control_projection("build_dashboard_autonomy", 
        organization_id=organization_id,
        source="novaride_phase2_autonomous_dispatch",
        limit=24,
    )
    autonomy = autonomy_surface["autonomy"]
    driver_allocation = autonomy_surface.get("driver_allocation", {})
    if not autonomy.get("safe_to_autorun", False):
        event = publish_phase2_event(
            organization_id=organization_id,
            event_type="autonomous_dispatch_held",
            ride_id=ride_id,
            payload={
                "ride": ride,
                "autonomy": autonomy,
                "driver_allocation": driver_allocation,
                "reason": autonomy.get("summary"),
            },
        )
        _store().record_audit_event(
            organization_id=organization_id,
            event_type="phase2.autonomous_dispatch_held",
            actor_user_id=actor_user_id,
            actor_role=actor_role,
            target=ride_id,
            status="recorded",
            payload={
                "ride": ride,
                "autonomy": autonomy,
                "driver_allocation": driver_allocation,
                "event": event,
            },
        )
        return {
            "ride": ride,
            "dispatch": None,
            "autonomy": autonomy,
            "driver_allocation": driver_allocation,
            "executed": False,
            "held_reason": autonomy.get("summary"),
            "event": event,
        }

    dispatch = dispatch_ride(
        organization_id=organization_id,
        ride_id=ride_id,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        payment_provider=payment_provider,
    )
    event = publish_phase2_event(
        organization_id=organization_id,
        event_type="autonomous_dispatch_executed",
        ride_id=ride_id,
        payload={
            "ride": dispatch["ride"],
            "dispatch": dispatch,
            "autonomy": autonomy,
            "driver_allocation": driver_allocation,
        },
    )
    _store().record_audit_event(
        organization_id=organization_id,
        event_type="phase2.autonomous_dispatch_executed",
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target=ride_id,
        status="recorded",
        payload={
            "ride": dispatch["ride"],
            "dispatch": dispatch,
            "autonomy": autonomy,
            "driver_allocation": driver_allocation,
            "event": event,
        },
    )
    return {
        "ride": dispatch["ride"],
        "dispatch": dispatch,
        "autonomy": autonomy,
        "driver_allocation": driver_allocation,
        "executed": True,
        "event": event,
    }


def build_phase2_status(
    *,
    organization_id: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    org_id = organization_id or DEFAULT_ORGANIZATION_ID
    phase1_status = build_phase1_status(organization_id=org_id, limit=limit)
    drivers = list_driver_presence(organization_id=org_id, limit=limit)
    assignments = _store().list_dispatch_assignments(organization_id=org_id, limit=limit)
    authorizations = _store().list_external_payment_authorizations(organization_id=org_id, limit=limit)
    captures = _store().list_external_payment_captures(organization_id=org_id, limit=limit)
    audit_log = build_audit_log(organization_id=org_id)
    audit_entries = audit_log["entries"]
    readiness = {
        "drivers_online": any(driver["status"] == "online" for driver in drivers),
        "dispatch_assigned": any(item["status"] in {"assigned", "accepted"} for item in assignments),
        "ride_assigned": any(item["status"] in {"assigned", "accepted"} for item in assignments),
        "driver_acceptance_recorded": any(item["status"] == "accepted" for item in assignments),
        "driver_arrival_recorded": any(
            entry["event_type"] == "phase2.driver_arrived" for entry in audit_entries
        ),
        "trip_started": any(entry["event_type"] == "phase2.trip_started" for entry in audit_entries),
        "trip_lifecycle_continues": any(
            entry["event_type"] == "phase2.trip_completed" for entry in audit_entries
        ),
        "external_payment_authorized": len(authorizations) >= 1,
        "payment_captured": len(captures) >= 1,
        "ledger_updated": phase1_status["readiness"]["transactions_recorded"],
        "all_actions_audited": audit_log["count"] >= phase1_status["audit_log"]["count"],
        "tenant_isolation_preserved": all(
            item["organization_id"] == org_id
            for item in drivers + assignments + authorizations + captures
        ),
    }
    return {
        "view": "novaride_phase2_status",
        "phase": "2",
        "platform": "NovaRide Phase 2",
        "organization_id": org_id,
        "phase1": phase1_status,
        "drivers": drivers,
        "dispatch_assignments": assignments,
        "payment_authorizations": authorizations,
        "payment_captures": captures,
        "audit_log": audit_log,
        "readiness": readiness,
        "ready": all(readiness.values()),
        "read_only": True,
        "projection_only": True,
        "governance_linked": True,
        "creates_authority": False,
    }


__all__ = [
    "PHASE2_TOPIC",
    "authorize_external_payment",
    "build_phase2_status",
    "capture_external_payment",
    "complete_trip",
    "dispatch_ride",
    "driver_accept",
    "driver_arrive",
    "driver_location",
    "driver_offline",
    "driver_online",
    "driver_reject",
    "publish_phase2_event",
    "execute_bounded_autonomous_dispatch",
    "request_and_dispatch_ride",
    "start_trip",
]
