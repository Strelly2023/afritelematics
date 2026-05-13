from ecosystems.afriride.core.infrastructure.matching.driver_matcher import match_driver


def dispatch_assign_driver(
    ride_id: str,
    store,
    geo_index,
    presence_service,
    radius: float | None = None,
):
    """
    Dispatch decision: select the best driver for a ride.

    Responsibilities:
    - Read event history
    - Extract pickup location
    - Find nearby drivers
    - Filter available drivers
    - Determine best driver (deterministic)

    Does NOT:
    - persist events
    - modify aggregate
    - update projections
    """

    # --------------------------------------------------
    # 1. LOAD EVENT HISTORY
    # --------------------------------------------------
    events = store.load(ride_id)

    if not events:
        raise Exception(f"Ride {ride_id} not found")

    # --------------------------------------------------
    # 2. EXTRACT PICKUP LOCATION
    # --------------------------------------------------
    pickup = None

    for event in events:
        if event.type == "RideRequested":
            pickup = event.payload["pickup"]
            break

    if pickup is None:
        raise Exception("Pickup location missing")

    # --------------------------------------------------
    # 3. FETCH NEARBY DRIVERS
    # --------------------------------------------------
    nearby_drivers = geo_index.find_nearby(
        pickup=pickup,
        radius=radius,
    )

    if not nearby_drivers:
        raise Exception("No nearby drivers")

    # --------------------------------------------------
    # 4. FILTER AVAILABLE DRIVERS
    # --------------------------------------------------
    available_drivers = [
        d for d in nearby_drivers
        if presence_service.is_available(d["id"])
    ]

    if not available_drivers:
        raise Exception("No available drivers")

    # --------------------------------------------------
    # 5. DETERMINE BEST DRIVER
    # --------------------------------------------------
    driver = match_driver(
        available_drivers,
        pickup,
    )

    if not driver:
        raise Exception("Driver matching failed")

    # --------------------------------------------------
    # ✅ RETURN DECISION ONLY
    # --------------------------------------------------
    return {
        "driver_id": driver["id"],
        "distance": driver.get("distance"),
    }
