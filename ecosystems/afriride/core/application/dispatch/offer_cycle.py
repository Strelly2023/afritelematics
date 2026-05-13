from ecosystems.afriride.core.domain.events.ride_events import (
    DriverOffered,
    OfferExpired,
)


# --------------------------------------------------
# START OFFER CYCLE
# --------------------------------------------------
def start_offer_cycle(ride_id, driver_queue):
    """
    Start the dispatch offer cycle.

    Deterministic:
    - always selects first driver (attempt=0)
    - driver_queue MUST already be sorted
    """

    if not driver_queue:
        raise Exception("No drivers to offer")

    first_driver = driver_queue[0]

    if "id" not in first_driver:
        raise Exception("Invalid driver object: missing 'id'")

    return DriverOffered(
        ride_id=ride_id,
        driver_id=first_driver["id"],
        attempt=0
    )


# --------------------------------------------------
# HANDLE OFFER TIMEOUT
# --------------------------------------------------
def handle_offer_timeout(ride_id, driver_queue, attempt):
    """
    Handle timeout of a driver offer.

    Produces:
    - OfferExpired (always)
    - DriverOffered (if more drivers exist)

    Fully deterministic:
    Same queue + same attempt → same output
    """

    if attempt < 0 or attempt >= len(driver_queue):
        raise Exception(f"Invalid attempt index: {attempt}")

    expired_driver = driver_queue[attempt]

    if "id" not in expired_driver:
        raise Exception("Invalid driver object: missing 'id'")

    # ---------------------------------------------
    # 1. expire current driver
    # ---------------------------------------------
    expire_event = OfferExpired(
        ride_id=ride_id,
        driver_id=expired_driver["id"],
        attempt=attempt
    )

    # ---------------------------------------------
    # 2. compute next attempt
    # ---------------------------------------------
    next_attempt_index = attempt + 1

    # ---------------------------------------------
    # 3. no more drivers → stop cycle
    # ---------------------------------------------
    if next_attempt_index >= len(driver_queue):
        return [expire_event]

    # ---------------------------------------------
    # 4. offer next driver
    # ---------------------------------------------
    next_driver = driver_queue[next_attempt_index]

    if "id" not in next_driver:
        raise Exception("Invalid driver object: missing 'id'")

    offer_event = DriverOffered(
        ride_id=ride_id,
        driver_id=next_driver["id"],
        attempt=next_attempt_index
    )

    return [expire_event, offer_event]