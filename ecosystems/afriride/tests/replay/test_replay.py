from ecosystems.core.infrastructure.persistence.event_store import EventStore
from ecosystems.afriride.core.domain.aggregates.repository import load_aggregate


def test_replay_consistency():

    store = EventStore()
    ride_id = "ride_001"

    # --------------------------------------------------
    # Create events manually through aggregate
    # --------------------------------------------------
    from ecosystems.afriride.core.domain.aggregates.ride_aggregate import RideAggregate

    agg = RideAggregate()

    e1 = agg.request_ride(
        ride_id,
        "r1",
        {"lat": 0, "lng": 0},
        {"lat": 1, "lng": 1}
    )
    store.append(ride_id, 0, e1)

    agg = load_aggregate(store, ride_id)

    e2 = agg.assign_driver(ride_id, "d1")
    store.append(ride_id, 1, e2)

    # --------------------------------------------------
    # Replay multiple times
    # --------------------------------------------------
    for _ in range(5):
        replay_agg = load_aggregate(store, ride_id)

        assert replay_agg.state == "ASSIGNED"
        assert replay_agg.version == 2