# 📁 ecosystems/afriride/application/commands/request_ride.py

from ecosystems.afriride.domain.aggregates.repository import (
    load_aggregate,
)

from ecosystems.afriride.domain.events.ride_events import (
    RideRequested,
)


def request_ride(command: dict, store) -> RideRequested:
    """
    Command handler for requesting a ride.

    ARCHITECTURAL FLOW:
        LOAD → REPLAY → EXECUTE → APPEND → PUBLISH

    RESPONSIBILITIES:
    - reconstruct aggregate from event history
    - validate command intent
    - emit domain event
    - persist event with optimistic concurrency

    GUARANTEES:
    - deterministic replay
    - optimistic concurrency safety
    - aggregate invariants enforced
    - event-store authoritative ordering
    """

    # --------------------------------------------------
    # EXTRACT COMMAND DATA
    # --------------------------------------------------
    ride_id = command["ride_id"]
    rider_id = command["rider_id"]
    pickup = command["pickup"]
    dropoff = command["dropoff"]

    # --------------------------------------------------
    # 1. LOAD & REPLAY
    # --------------------------------------------------
    # Rebuild authoritative aggregate state
    # from event history.
    #
    # aggregate.state = reduce(events)
    #
    agg = load_aggregate(store, ride_id)

    # --------------------------------------------------
    # 2. EXECUTE DOMAIN COMMAND
    # --------------------------------------------------
    # Aggregate validates invariants
    # and emits exactly one event.
    #
    event = agg.request_ride(
        ride_id=ride_id,
        rider_id=rider_id,
        pickup=pickup,
        dropoff=dropoff,
    )

    # --------------------------------------------------
    # 3. PERSIST EVENT
    # --------------------------------------------------
    # expected_version prevents concurrent writes:
    #
    # stream_version must match
    # aggregate reconstructed version.
    #
    # Since apply(event) already incremented:
    #
    # expected_version = agg.version - 1
    #
    store.append(
        stream_id=ride_id,
        expected_version=agg.version - 1,
        event=event,
    )

    # --------------------------------------------------
    # 4. RETURN DOMAIN EVENT
    # --------------------------------------------------
    return event