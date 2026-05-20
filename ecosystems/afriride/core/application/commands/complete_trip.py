# 📁 ecosystems/afriride/application/commands/complete_trip.py

from ecosystems.afriride.domain.aggregates.repository import (
    load_aggregate,
)

from ecosystems.afriride.domain.events.ride_events import (
    TripCompleted,
)


def complete_trip(command: dict, store) -> TripCompleted:
    """
    Command handler for completing a trip.

    ARCHITECTURAL FLOW:
        LOAD → REPLAY → EXECUTE → APPEND → PUBLISH

    RESPONSIBILITIES:
    - reconstruct aggregate state from event history
    - validate trip completion intent
    - emit TripCompleted event
    - persist event with optimistic concurrency

    GUARANTEES:
    - deterministic replay
    - invariant-safe execution
    - concurrency-safe persistence
    - authoritative event ordering
    """

    # --------------------------------------------------
    # EXTRACT COMMAND DATA
    # --------------------------------------------------
    ride_id = command["ride_id"]

    # --------------------------------------------------
    # 1. LOAD & REPLAY
    # --------------------------------------------------
    # Reconstruct authoritative aggregate state
    # from historical events.
    #
    # aggregate.state = reduce(events)
    #
    agg = load_aggregate(store, ride_id)

    # --------------------------------------------------
    # 2. EXECUTE DOMAIN COMMAND
    # --------------------------------------------------
    # Aggregate validates:
    # - ride existence
    # - identity consistency
    # - transition invariants
    #
    # Then emits TripCompleted event.
    #
    event = agg.complete_trip(
        ride_id=ride_id,
    )

    # --------------------------------------------------
    # 3. PERSIST EVENT
    # --------------------------------------------------
    # aggregate.version already includes
    # the newly applied event.
    #
    # expected_version protects against:
    # - concurrent modifications
    # - stale aggregate writes
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