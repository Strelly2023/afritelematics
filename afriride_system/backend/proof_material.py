"""Shared proof-material helpers for ride-scoped replay, evidence, and receipts."""

from __future__ import annotations

from afriride_system.backend.api_gateway.gateway import AfriRideGateway
from afriride_system.backend.state import RideSession
from afriride_system.backend.trace_enforcement import (
    TraceEvent,
    TraceEventLog,
    __doc_authority__,
    __doc_version__,
    __governed_invariants__,
    authority_envelope,
    stable_hash,
)


def completed_ride(gateway: AfriRideGateway, ride_id: str) -> RideSession | None:
    ride = gateway.dispatcher.rides.get(ride_id)
    if ride is None or ride.status != "COMPLETED":
        return None
    return ride


def proof_events_for_ride(
    trace_log: TraceEventLog,
    ride: RideSession,
) -> tuple[TraceEvent, ...]:
    events = trace_log.events_for_ride(ride.ride_id)
    if events:
        return events
    return synthetic_trace_for_ride(ride)


def synthetic_trace_for_ride(ride: RideSession) -> tuple[TraceEvent, ...]:
    mapping = {
        "ride_requested": ("REQUESTED", "rider", ride.passenger_id, "POST /passenger/request-ride"),
        "driver_assigned": (
            "DRIVER_ACCEPTED",
            "driver",
            ride.assigned_driver or "driver",
            f"POST /ride/{ride.ride_id}/accept",
        ),
        "driver_arrived": (
            "ARRIVED",
            "driver",
            ride.assigned_driver or "driver",
            f"POST /ride/{ride.ride_id}/arrive",
        ),
        "trip_started": (
            "STARTED",
            "driver",
            ride.assigned_driver or "driver",
            f"POST /ride/{ride.ride_id}/start",
        ),
        "trip_completed": (
            "COMPLETED",
            "driver",
            ride.assigned_driver or "driver",
            f"POST /ride/{ride.ride_id}/complete",
        ),
        "ride_canceled": (
            "CANCELLED",
            "rider",
            ride.passenger_id,
            "POST /passenger/cancel",
        ),
    }
    authority_hash = authority_envelope(
        doc_id=__doc_authority__,
        doc_version=__doc_version__,
        governed_invariants=__governed_invariants__,
        surface="trace_event",
    )["authority_hash"]
    previous_hash: str | None = None
    trace_events: list[TraceEvent] = []
    for index, event_name in enumerate(ride.events, start=1):
        transition, actor_type, actor_id, action = mapping.get(
            event_name,
            ("UNKNOWN", "operator", "system", f"EVENT {event_name}"),
        )
        event_hash = stable_hash(
            {
                "event_id": f"{ride.ride_id}-synthetic-{index}",
                "sequence_id": index,
                "device_id": "backend-synthesized",
                "actor_type": actor_type,
                "actor_id": actor_id,
                "action": action,
                "payload": {"ride_id": ride.ride_id},
                "local_timestamp": "2026-06-01T00:00:00Z",
                "normalized_timestamp": "2026-06-01T00:00:00Z",
                "app_version": "0.1",
                "test_mode": False,
                "ride_id": ride.ride_id,
                "transition": transition,
                "previous_hash": previous_hash,
                "authority_hash": authority_hash,
            }
        )
        trace_events.append(
            TraceEvent(
                event_id=f"{ride.ride_id}-synthetic-{index}",
                sequence_id=index,
                device_id="backend-synthesized",
                actor_type=actor_type,
                actor_id=str(actor_id),
                action=action,
                payload={"ride_id": ride.ride_id},
                local_timestamp="2026-06-01T00:00:00Z",
                normalized_timestamp="2026-06-01T00:00:00Z",
                app_version="0.1",
                test_mode=False,
                ride_id=ride.ride_id,
                transition=transition,
                previous_hash=previous_hash,
                authority_hash=authority_hash,
                event_hash=event_hash,
            )
        )
        previous_hash = event_hash
    return tuple(trace_events)
