from ecosystems.afriride.domain.aggregates.repository import (
    load_aggregate,
)
from ecosystems.afriride.domain.events.ride_events import (
    DriverAccepted,
)
from ecosystems.afriride.domain.state.ride_state import (
    RideStatus,
)


def accept_driver(command, store):
    """
    Driver accepts an offer.

    Flow:
    LOAD → VALIDATE (intent invariants) → EMIT EVENT → STORE

    Guarantees:
    - Does NOT mutate state directly
    - Relies on aggregate + event replay for correctness
    - Emits a single event
    """

    ride_id = command["ride_id"]
    driver_id = command["driver_id"]
    attempt = command["attempt"]

    # --------------------------------------------------
    # 1. LOAD AGGREGATE (REPLAY)
    # --------------------------------------------------
    agg = load_aggregate(store, ride_id)

    # --------------------------------------------------
    # 2. VALIDATE INTENT (COMMAND LAYER ONLY)
    # --------------------------------------------------
    if agg.state != RideStatus.REQUESTED:
        raise Exception("Ride is no longer accepting offers")

    # Optional: defensive check for terminal safety
    if agg.state == RideStatus.COMPLETED:
        raise Exception("Cannot accept driver for completed ride")

    # --------------------------------------------------
    # 3. CREATE EVENT
    # --------------------------------------------------
    event = DriverAccepted(
        ride_id=ride_id,
        driver_id=driver_id,
        attempt=attempt,
    )

    # --------------------------------------------------
    # 4. PERSIST EVENT (SOURCE OF TRUTH)
    # --------------------------------------------------
    store.append(
        ride_id,
        agg.version,
        event,
    )

    # --------------------------------------------------
    # 5. RETURN EVENT
    # --------------------------------------------------
    return event