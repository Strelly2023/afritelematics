# 📁 ecosystems/afriride/application/commands/cancel_trip.py

from ecosystems.afriride.domain.aggregates.repository import (
    load_aggregate,
)

from ecosystems.afriride.domain.events.ride_events import (
    TripCancelled,
)


def cancel_trip(command: dict, store) -> TripCancelled:
    """
    Command handler for cancelling a trip.

    ARCHITECTURAL FLOW:
        LOAD → REPLAY → EXECUTE → APPEND → PUBLISH

    RESPONSIBILITIES:
    - reconstruct aggregate from event history
    - validate cancellation intent
    - emit TripCancelled event
    - persist event using optimistic concurrency

    GUARANTEES:
    - deterministic replay
    - invariant-safe execution
    - event-store authoritative ordering
    - concurrency-safe persistence
    """

    # --------------------------------------------------
    # EXTRACT COMMAND DATA
    # --------------------------------------------------
    ride_id = command["ride_id"]
    reason = command.get("reason")

    # --------------------------------------------------
    # 1. LOAD & REPLAY
    # --------------------------------------------------
    # Rebuild aggregate state from authoritative
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
    # - ride not terminal
    #
    # Then emits TripCancelled event.
    #
    event = agg.cancel_trip(
        ride_id=ride_id,
        reason=reason,
    )

    # --------------------------------------------------
    # 3. PERSIST EVENT
    # --------------------------------------------------
    # aggregate.version already includes
    # the newly applied event.
    #
    # expected_version protects against:
    # - concurrent writes
    # - stale aggregate state
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