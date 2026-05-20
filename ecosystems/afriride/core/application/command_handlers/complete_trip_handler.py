from ecosystems.afriride.core.application.commands.complete_trip import (
    complete_trip,
)
from afritech.core.infrastructure.persistence.event_store import EventStore


def handle_complete_trip(command: dict, store: EventStore):
    """
    Command handler for completing a trip.

    Flow:
    VALIDATE → EXECUTE COMMAND → APPEND EVENT → (OPTIONAL PUBLISH)

    Responsibilities:
    - Marks the end of a ride lifecycle
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
    event = complete_trip(command, store)

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