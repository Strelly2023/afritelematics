from ecosystems.core.infrastructure.persistence.event_store import EventStore
from ecosystems.afriride.core.domain.aggregates.repository import load_aggregate
from ecosystems.afriride.core.domain.aggregates.ride_aggregate import RideAggregate


def test_full_lifecycle():

    store = EventStore()
    ride_id = "ride_001"

    # --------------------------------------------------
    # REQUEST
    # --------------------------------------------------
    agg = RideAggregate()
    e1 = agg.request_ride(
        ride_id,
        "r1",
        {"lat": 0, "lng": 0},
        {"lat": 1, "lng": 1}
    )
    store.append(ride_id, 0, e1)

    # --------------------------------------------------
    # ASSIGN
    # --------------------------------------------------
    agg = load_aggregate(store, ride_id)
    e2 = agg.assign_driver(ride_id, "d1")
    store.append(ride_id, 1, e2)

    # --------------------------------------------------
    # START
    # --------------------------------------------------
    agg = load_aggregate(store, ride_id)
    e3 = agg.start_trip(ride_id)
    store.append(ride_id, 2, e3)

    # --------------------------------------------------
    # COMPLETE
    # --------------------------------------------------
    agg = load_aggregate(store, ride_id)
    e4 = agg.complete_trip(ride_id)
    store.append(ride_id, 3, e4)

    # --------------------------------------------------
    # FINAL REPLAY
    # --------------------------------------------------
    final_agg = load_aggregate(store, ride_id)

    assert final_agg.state == "COMPLETED"
    assert final_agg.version == 4