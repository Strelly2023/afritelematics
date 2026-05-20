from ecosystems.afriride.domain.aggregates.ride_aggregate import RideAggregate


def load_aggregate(store, ride_id):
    """
    Reconstruct aggregate from event store

    This is the ONLY valid way to restore state.
    """

    agg = RideAggregate()

    events = store.load(ride_id)

    agg.apply_all(events)

    return agg
