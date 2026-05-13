from ecosystems.afriride.core.application.commands.start_trip import (
    start_trip,
)
from ecosystems.core.infrastructure.persistence.event_store import EventStore


def handle_start_trip(command: dict, store: EventStore):
    """
    Command handler for starting a trip.

    Flow:
    VALIDATE → EXECUTE COMMAND → APPEND EVENT → (OPTIONAL PUBLISH)

    Responsibilities:
    - Marks the beginning of a ride in progress
    - No business logic
    - No direct state mutation
    - Delegates to domain command
    """

    # --------------------------------------------------
    # 1. VALIDATION (STRUCTURAL ONLY)
    # --------------------------------------------------
    required_fields = ["ride_id"]

    for field in required_fields:
        if field not in command:
            raise Exception(f"{field} is required")

    # --------------------------------------------------
    # 2. EXECUTE DOMAIN COMMAND
    # --------------------------------------------------
    event = start_trip(command, store)

    # --------------------------------------------------
    # 3. OPTIONAL: EVENT BUS (FUTURE SCALING)
    # --------------------------------------------------
    # Hook for async streaming / distributed systems
    #
    # if hasattr(store, "event_bus") and store.event_bus:
    #     store.event_bus.publish(event)

    # --------------------------------------------------
    # 4. RETURN RESULT
    # --------------------------------------------------
    return {
        "status": "success",
        "event_type": event.type,
        "ride_id": event.payload["ride_id"],
        "event_id": event.event_id,
    }
