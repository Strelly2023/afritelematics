from evidence.models import EventLog
from realtime.events import broadcast_ride_event

from .matching import find_available_driver


def dispatch_ride(ride, actor):
    """Assign a driver and emit non-authoritative realtime projections.

    Canonical truth is recorded in EventLog. WebSocket broadcasts are only
    visibility surfaces for mobile/operator clients.
    """

    driver = find_available_driver()

    if driver is None:
        EventLog.objects.create(
            ride=ride,
            event_type="dispatch_failed",
            actor=actor,
            metadata={"reason": "no_available_driver"},
        )

        broadcast_ride_event(
            ride_id=ride.id,
            event_type="dispatch_failed",
            payload={"reason": "no_available_driver"},
        )

        return None

    EventLog.objects.create(
        ride=ride,
        event_type="ride_assigned",
        actor=actor,
        metadata={"driver_id": driver.id},
    )

    broadcast_ride_event(
        ride_id=ride.id,
        event_type="ride_assigned",
        payload={"ride_id": ride.id, "driver_id": driver.id},
    )

    return driver
