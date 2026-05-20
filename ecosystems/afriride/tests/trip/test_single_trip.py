from afritech.core.infrastructure.persistence.event_store import EventStore

from ecosystems.afriride.core.application.commands.request_ride import request_ride
from ecosystems.afriride.core.application.commands.assign_driver import assign_driver

from ecosystems.afriride.domain.aggregates.repository import load_aggregate

from ecosystems.afriride.core.infrastructure.geo.geo_index import DriverGeoIndex
from ecosystems.afriride.core.infrastructure.presence.driver_presence import DriverPresenceService


# --------------------------------------------------
# SINGLE TRIP FLOW TEST (END-TO-END)
# --------------------------------------------------
def test_single_trip_flow():

    store = EventStore()
    ride_id = "ride_001"

    # --------------------------------------------------
    # 0. INFRA DEPENDENCIES (REALISTIC CONTEXT)
    # --------------------------------------------------
    geo_index = DriverGeoIndex()
    presence_service = DriverPresenceService()

    # register available drivers
    geo_index.update_driver("d1", 0.1, 0.1)
    geo_index.update_driver("d2", 5, 5)

    presence_service.mark_online("d1")
    presence_service.mark_online("d2")

    # --------------------------------------------------
    # 1. REQUEST RIDE
    # --------------------------------------------------
    request_event = request_ride(
        {
            "ride_id": ride_id,
            "rider_id": "r1",
            "pickup": {"lat": 0, "lng": 0},
            "dropoff": {"lat": 1, "lng": 1},
        },
        store,
    )

    assert request_event.type == "RideRequested"

    # --------------------------------------------------
    # 2. ASSIGN DRIVER (deterministic matching)
    # --------------------------------------------------
    assign_event = assign_driver(
        {
            "ride_id": ride_id,
        },
        store,
        geo_index,
        presence_service,
    )

    assert assign_event.type == "DriverAssigned"

    # --------------------------------------------------
    # 3. REPLAY AGGREGATE
    # --------------------------------------------------
    agg = load_aggregate(store, ride_id)

    assert agg.state == "ASSIGNED"
    assert agg.version == 2

    # --------------------------------------------------
    # 4. FINAL INTEGRITY CHECK
    # --------------------------------------------------
    events = store.load(ride_id)

    assert len(events) == 2
    assert events[0].type == "RideRequested"
    assert events[1].type == "DriverAssigned"