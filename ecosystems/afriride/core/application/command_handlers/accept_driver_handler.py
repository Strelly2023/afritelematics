from ecosystems.afriride.core.application.commands.accept_driver import (
    accept_driver,
)
from afritech.core.infrastructure.persistence.event_store import EventStore


def handle_accept_driver(command: dict, store: EventStore):
    """
    Command handler for driver accepting an offer.

    Flow:
    VALIDATE → EXECUTE COMMAND → APPEND EVENT → (OPTIONAL PUBLISH)

    Responsibilities:
    - Entry point for driver acceptance
    - No business logic
    - No state mutation directly
    - Delegates to domain command
    """

    # --------------------------------------------------
    # 1. VALIDATION (STRUCTURAL ONLY)
    # --------------------------------------------------
    required_fields = ["ride_id", "driver_id", "attempt"]

    for field in required_fields:
        if field not in command:
            raise Exception(f"{field} is required")

    # --------------------------------------------------
    # 2. EXECUTE DOMAIN COMMAND
    # --------------------------------------------------
    event = accept_driver(command, store)

    # --------------------------------------------------
    # 3. OPTIONAL: EVENT BUS (FUTURE SCALING)
    # --------------------------------------------------
    # Hook for async streaming / distributed architecture
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
        "driver_id": event.payload["driver_id"],
        "attempt": event.payload["attempt"],
        "event_id": event.event_id,
    }