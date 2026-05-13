from ecosystems.afriride.core.application.commands.request_ride import (
    request_ride,
)
from ecosystems.core.infrastructure.persistence.event_store import EventStore


def handle_request_ride(command: dict, store: EventStore):
    """
    Command handler for requesting a ride.

    Flow:
    VALIDATE → EXECUTE COMMAND → APPEND EVENT → (OPTIONAL PUBLISH)

    Responsibilities:
    - Entry point for write side
    - No business logic
    - No state mutation directly
    - Delegates to domain command
    """

    # --------------------------------------------------
    # 1. VALIDATION (STRUCTURAL ONLY)
    # --------------------------------------------------
    required_fields = ["rider_id", "pickup", "dropoff"]

    for field in required_fields:
        if field not in command:
            raise Exception(f"{field} is required")

    # ride_id is optional (auto-generated if missing)
    ride_id = command.get("ride_id")

    # --------------------------------------------------
    # 2. EXECUTE DOMAIN COMMAND
    # --------------------------------------------------
    event = request_ride(command, store)

    # --------------------------------------------------
    # 3. OPTIONAL: EVENT BUS (FUTURE SCALING)
    # --------------------------------------------------
    # If your EventStore has streaming later, this is the hook
    # Example:
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