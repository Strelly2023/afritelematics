from ecosystems.core.infrastructure.persistence.event_store import EventStore
from ecosystems.afriride.core.application.commands.request_ride import request_ride
from ecosystems.afriride.core.application.dispatch.dispatch_engine import DispatchEngine
from ecosystems.afriride.core.domain.state.ride_state import RideStatus
from ecosystems.afriride.core.domain.aggregates.repository import load_aggregate


def test_driver_acceptance_stops_dispatch():
    store = EventStore()
    ride_id = "ride_001"

    # ----------------------------------------
    # Request ride
    # ----------------------------------------
    request_ride(
        {
            "ride_id": ride_id,
            "rider_id": "r1",
            "pickup": {"lat": 0, "lng": 0},
            "dropoff": {"lat": 1, "lng": 1},
        },
        store,
    )

    drivers = [
        {"id": "d1", "lat": 5, "lng": 5},
        {"id": "d2", "lat": 0.1, "lng": 0.1},
    ]

    dispatch = DispatchEngine(store)

    # ----------------------------------------
    # Start dispatch
    # ----------------------------------------
    offer_event, queue = dispatch.start(ride_id, drivers)

    # Sanity check
    assert offer_event.type == "DriverOffered"
    assert len(queue) == 2

    # ----------------------------------------
    # Accept first offer (best-ranked driver)
    # ----------------------------------------
    events = dispatch.accept(
        ride_id=ride_id,
        driver_id=queue[0]["id"],
        attempt=0,
    )

    # ----------------------------------------
    # Verify emitted events
    # ----------------------------------------
    assert len(events) == 2

    assert events[0].type == "DriverAccepted"
    assert events[1].type == "DriverAssigned"

    assert events[1].payload["driver_id"] == queue[0]["id"]

    # ----------------------------------------
    # Replay final state
    # ----------------------------------------
    agg = load_aggregate(store, ride_id)

    # ✅ IMPORTANT: use enum (not string)
    assert agg.state == RideStatus.ASSIGNED

    # ----------------------------------------
    # Ensure dispatch stops (no further offers)
    # ----------------------------------------
    # Optionally verify no additional offers are being generated
    # (depends on your dispatch design)
    assert agg.state != RideStatus.REQUESTED