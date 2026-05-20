from afritech.core.infrastructure.persistence.event_store import EventStore
from ecosystems.afriride.core.application.commands.request_ride import request_ride
from ecosystems.afriride.core.application.dispatch.dispatch_engine import DispatchEngine


def test_dispatch_flow():
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

    # Validate first offer
    assert offer_event.type == "DriverOffered"
    assert len(queue) == 2

    # Ensure best driver (closest) is first
    assert queue[0]["id"] == "d2"

    # ----------------------------------------
    # Timeout → move to next driver
    # ----------------------------------------
    events = dispatch.timeout(ride_id, queue, attempt=0)

    # Validate event chain
    assert len(events) == 2

    assert events[0].type == "OfferExpired"
    assert events[1].type == "DriverOffered"

    # Ensure second driver is offered now
    assert events[0].payload["driver_id"] == queue[0]["id"]
    assert events[1].payload["driver_id"] == queue[1]["id"]

    # Ensure attempt increments correctly
    assert events[1].payload["attempt"] == 1