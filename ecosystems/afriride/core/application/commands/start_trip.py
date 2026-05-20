# 📁 ecosystems/afriride/application/commands/start_trip.py

from ecosystems.afriride.domain.aggregates.repository import (
    load_aggregate,
)

from ecosystems.afriride.domain.events.ride_events import (
    TripStarted,
)


def start_trip(command: dict, store) -> TripStarted:
    """
    Command handler for starting a trip.

    ARCHITECTURAL FLOW:
        LOAD → REPLAY → EXECUTE → APPEND → PUBLISH

    RESPONSIBILITIES:
    - reconstruct aggregate state from history
    - validate trip start intent
    - emit TripStarted event
    - persist event with optimistic concurrency

    GUARANTEES:
    - deterministic replay
    - invariant-safe execution
    - optimistic concurrency protection
    - event-store authoritative ordering
    """

    # --------------------------------------------------
    # EXTRACT COMMAND DATA
    # --------------------------------------------------
    ride_id = command["ride_id"]

    # --------------------------------------------------
    # 1. LOAD & REPLAY
    # --------------------------------------------------
    # Reconstruct aggregate from authoritative
    # event history.
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
    # - non-terminal state
    #
    # Then emits TripStarted event.
    #
    event = agg.start_trip(
        ride_id=ride_id,
    )

    # --------------------------------------------------
    # 3. PERSIST EVENT
    # --------------------------------------------------
    # Optimistic concurrency:
    #
    # aggregate.version already includes
    # the newly applied event.
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