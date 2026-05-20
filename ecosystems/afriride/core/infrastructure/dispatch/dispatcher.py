
from ecosystems.afriride.domain.events.ride_events import (
    DriverAssigned,
    DriverAccepted,

)

# --------------------------------------------------
# SINGLE ASSIGNMENT (PURE)
# --------------------------------------------------
def dispatch_driver(ride_id, driver):
    """
    Convert a selected driver into a DriverAssigned event.

    Pure function:
    - No randomness
    - No mutation
    - Deterministic output
    """

    if not driver:
        raise Exception("Cannot dispatch without driver")

    if "id" not in driver:
        raise Exception("Driver missing 'id' field")

    return DriverAssigned(
        ride_id=ride_id,
        driver_id=driver["id"]
    )


# --------------------------------------------------
# FULL ASSIGNMENT SEQUENCE (DETERMINISTIC ORDER)
# --------------------------------------------------
def build_assignment_sequence(ride_id, drivers):
    """
    Build a deterministic assignment sequence.

    This is used for:
    - fallback logic
    - dispatch retries
    - testing deterministic ordering

    Output:
    ordered list of DriverAssigned events
    """

    if not drivers:
        return []

    events = []

    for index, driver in enumerate(drivers):

        if "id" not in driver:
            raise Exception(f"Driver at position {index} missing 'id'")

        events.append(
            DriverAssigned(
                ride_id=ride_id,
                driver_id=driver["id"]
            )
        )

    return events


# --------------------------------------------------
# EXTRACT DRIVER IDS (UTILITY)
# --------------------------------------------------
def extract_driver_ids(drivers):
    """
    Utility helper for debugging / verification.

    Ensures deterministic identity sequence.
    """

    return [driver["id"] for driver in drivers if "id" in driver]


# --------------------------------------------------
# SAFE DRIVER VALIDATION
# --------------------------------------------------
def validate_driver(driver):
    """
    Defensive validation for driver object.
    """

    if not driver:
        raise Exception("Driver cannot be None")

    if "id" not in driver:
        raise Exception("Driver must contain 'id'")

    if "lat" not in driver or "lng" not in driver:
        raise Exception("Driver must contain 'lat' and 'lng'")

    return True





# --------------------------------------------------
# SHORTCUT: ACCEPT → ASSIGN TRANSFORMATION
# --------------------------------------------------

# --------------------------------------------------
# PURE DRIVER ASSIGNMENT TRANSFORMATION
# --------------------------------------------------
def accepted_to_assigned(event):
    """
    Convert DriverAccepted event into DriverAssigned event.

    Pure transformation:
    - Deterministic
    - No side effects
    - Used for fast-path assignment logic
    """

    if event.type != "DriverAccepted":
        raise Exception(
            f"Expected DriverAccepted event, got {event.type}"
        )

    return DriverAssigned(
        ride_id=event.payload["ride_id"],
        driver_id=event.payload["driver_id"],
    )
