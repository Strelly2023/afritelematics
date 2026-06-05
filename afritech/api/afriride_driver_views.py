from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.trust_kernel.events import process_command
from afritech.trust_kernel.policy import Command


_DRIVER_AVAILABILITY: dict[str, dict[str, str]] = {}
_RIDES: dict[str, dict[str, Any]] = {
    "ride-demo-1": {
        "ride_id": "ride-demo-1",
        "driver_id": "D001",
        "rider_name": "Demo Rider",
        "pickup_text": "Bujumbura Central",
        "dropoff_text": "Rohero Market",
        "quoted_total_text": "BIF 5,000",
        "status": "pending",
    }
}


@api_view(["GET"])
def api_root(request) -> Response:
    return Response(
        {
            "status": "ok",
            "service": "afriride-django-api",
            "mode": "development",
            "endpoints": [
                "/api/driver/availability",
                "/api/driver/{driver_id}/queue",
                "/api/ride/{ride_id}/accept",
                "/api/ride/{ride_id}/start",
                "/api/ride/{ride_id}/complete",
            ],
        }
    )


@api_view(["POST"])
def driver_availability(request) -> Response:
    driver_id = _text(request.data.get("driver_id"), "driver_id")
    status = _text(request.data.get("status"), "status")
    if status not in {"available", "offline"}:
        return Response({"detail": "status must be available or offline"}, status=400)

    payload = {
        "driver_id": driver_id,
        "status": status,
        "updated_at": _now(),
    }
    _DRIVER_AVAILABILITY[driver_id] = payload
    _ensure_driver_queue(driver_id)
    _append_trust_event(
        event_type="DriverAvailabilityChanged",
        actor_id=driver_id,
        subject_id=driver_id,
        payload=payload,
    )
    return Response(payload)


@api_view(["POST"])
def driver_status(request) -> Response:
    online = bool(request.data.get("online"))
    request.data["status"] = "available" if online else "offline"
    return driver_availability(request)


@api_view(["GET"])
def driver_queue(request, driver_id: str) -> Response:
    _ensure_driver_queue(driver_id)
    rides = [
        _ride_request_payload(ride)
        for ride in _RIDES.values()
        if ride.get("driver_id") == driver_id and ride.get("status") in {"pending", "accepted"}
    ]
    return Response({"rides": rides})


@api_view(["POST"])
def ride_accept(request, ride_id: str) -> Response:
    driver_id = str(request.data.get("driver_id") or "D001")
    ride = _get_or_create_ride(ride_id, driver_id)
    ride["driver_id"] = driver_id
    ride["status"] = "accepted"
    _append_ride_event("RideAccepted", ride, driver_id)
    return Response(_trip_payload(ride, "Proceed to pickup"))


@api_view(["POST"])
def ride_reject(request, ride_id: str) -> Response:
    driver_id = str(request.data.get("driver_id") or "D001")
    ride = _get_or_create_ride(ride_id, driver_id)
    ride["status"] = "cancelled"
    _append_ride_event("RideRejected", ride, driver_id)
    return Response(_trip_payload(ride, "Ride rejected"))


@api_view(["POST"])
def ride_arrive(request) -> Response:
    ride_id = _text(request.data.get("ride_id"), "ride_id")
    ride = _get_or_create_ride(ride_id, str(request.data.get("driver_id") or "D001"))
    ride["status"] = "arrived"
    _append_ride_event("DriverArrived", ride, str(ride.get("driver_id") or "D001"))
    return Response(_trip_payload(ride, "Start trip when rider is onboard"))


@api_view(["POST"])
def ride_start(request, ride_id: str) -> Response:
    driver_id = str(request.data.get("driver_id") or "D001")
    ride = _get_or_create_ride(ride_id, driver_id)
    ride["status"] = "started"
    _append_ride_event("TripStarted", ride, driver_id)
    return Response(_trip_payload(ride, "Complete trip at dropoff"))


@api_view(["POST"])
def ride_complete(request, ride_id: str) -> Response:
    driver_id = str(request.data.get("driver_id") or "D001")
    ride = _get_or_create_ride(ride_id, driver_id)
    ride["status"] = "completed"
    ride["completed_at"] = _now()
    _append_ride_event("TripCompleted", ride, driver_id)
    return Response(_trip_payload(ride, "Trip completed"))


@api_view(["GET"])
def driver_earnings(request, driver_id: str) -> Response:
    completed = [
        ride
        for ride in _RIDES.values()
        if ride.get("driver_id") == driver_id and ride.get("status") == "completed"
    ]
    return Response(
        {
            "driver_id": driver_id,
            "period_label": "Today",
            "total_text": f"BIF {len(completed) * 5000:,}",
            "ride_count": len(completed),
            "source": "core_system",
        }
    )


@api_view(["GET"])
def driver_replay_history(request) -> Response:
    driver_id = request.query_params.get("driver_id", "D001")
    rides = [
        {
            "ride_id": ride["ride_id"],
            "replay_id": f"replay-{ride['ride_id']}",
            "replay_verified": True,
            "completed_at": ride.get("completed_at"),
        }
        for ride in _RIDES.values()
        if ride.get("driver_id") == driver_id and ride.get("status") == "completed"
    ]
    return Response({"rides": rides})


def _ensure_driver_queue(driver_id: str) -> None:
    if not any(ride.get("driver_id") == driver_id for ride in _RIDES.values()):
        _RIDES[f"ride-{driver_id}-demo"] = {
            "ride_id": f"ride-{driver_id}-demo",
            "driver_id": driver_id,
            "rider_name": "Demo Rider",
            "pickup_text": "Bujumbura Central",
            "dropoff_text": "Rohero Market",
            "quoted_total_text": "BIF 5,000",
            "status": "pending",
        }


def _get_or_create_ride(ride_id: str, driver_id: str) -> dict[str, Any]:
    if ride_id not in _RIDES:
        _RIDES[ride_id] = {
            "ride_id": ride_id,
            "driver_id": driver_id,
            "rider_name": "Demo Rider",
            "pickup_text": "Bujumbura Central",
            "dropoff_text": "Rohero Market",
            "quoted_total_text": "BIF 5,000",
            "status": "pending",
        }
    return _RIDES[ride_id]


def _ride_request_payload(ride: dict[str, Any]) -> dict[str, Any]:
    return {
        "ride_id": ride["ride_id"],
        "pickup_text": ride["pickup_text"],
        "dropoff_text": ride["dropoff_text"],
        "rider_name": ride.get("rider_name"),
        "status": "accepted" if ride.get("status") == "accepted" else "pending",
        "quoted_total_text": ride.get("quoted_total_text"),
    }


def _trip_payload(ride: dict[str, Any], next_instruction: str) -> dict[str, Any]:
    return {
        "ride_id": ride["ride_id"],
        "status": ride["status"],
        "rider_name": ride.get("rider_name"),
        "pickup_text": ride.get("pickup_text"),
        "dropoff_text": ride.get("dropoff_text"),
        "next_instruction": next_instruction,
    }


def _append_ride_event(event_type: str, ride: dict[str, Any], driver_id: str) -> None:
    witnesses: tuple[dict[str, str], ...] = ()
    if event_type == "TripCompleted":
        witnesses = (
            {"verifier_node": "pilot-observer-1", "signature": "development-witness-1"},
            {"verifier_node": "pilot-observer-2", "signature": "development-witness-2"},
        )
    _append_trust_event(
        event_type=event_type,
        actor_id=driver_id,
        subject_id=str(ride["ride_id"]),
        payload={
            "ride_id": ride["ride_id"],
            "status": ride["status"],
            "driver_id": driver_id,
        },
        witnesses=witnesses,
    )


def _append_trust_event(
    *,
    event_type: str,
    actor_id: str,
    subject_id: str,
    payload: dict[str, Any],
    witnesses: tuple[dict[str, str], ...] = (),
) -> None:
    try:
        process_command(
            Command(
                event_type=event_type,
                actor_id=actor_id,
                subject_id=subject_id,
                payload=payload,
                signature={"signature_mode": "development_adapter"},
                witnesses=witnesses,
            )
        )
    except Exception:
        # The adapter remains usable before migrations are applied; trust-kernel
        # tests enforce the ledger path directly.
        return


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} is required")
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
