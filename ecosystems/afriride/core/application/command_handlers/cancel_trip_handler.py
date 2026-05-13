from ecosystems.afriride.core.application.commands.cancel_trip import (
    cancel_trip,
)
from ecosystems.core.infrastructure.persistence.event_store import EventStore


def handle_cancel_trip(command: dict, store: EventStore):
    """
    Command handler for cancelling a trip.

    Flow:
    VALIDATE → EXECUTE COMMAND → APPEND EVENT → (OPTIONAL PUBLISH)

    Responsibilities:
    - Cancels a ride before or during execution
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

    ride_id = command["ride_id"]
    reason = command.get("reason")

    # --------------------------------------------------
    # 2. EXECUTE DOMAIN COMMAND
    # --------------------------------------------------
    event = cancel_trip(
        {
            "ride_id": ride_id,
            "reason": reason,
        },
        store,
    )

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
        "reason": event.payload.get("reason"),
        "event_id": event.event_id,
    }
