from ecosystems.afriride.core.domain.aggregates.repository import load_aggregate
from ecosystems.afriride.core.infrastructure.matching.driver_matcher import match_driver
from ecosystems.afriride.core.infrastructure.geo.geo_index import DriverGeoIndex
from ecosystems.afriride.core.infrastructure.presence.driver_presence import DriverPresenceService


def assign_driver(
    command,
    store,
    geo_index: DriverGeoIndex,
    presence_service: DriverPresenceService,
):
    """
    Assign a driver to a ride.

    Deterministic execution flow:

    LOAD
    → REPLAY
    → EXTRACT PICKUP
    → GEO QUERY
    → FILTER AVAILABLE DRIVERS
    → DETERMINISTIC MATCH
    → AGGREGATE VALIDATION
    → EVENT
    → STORE
    → UPDATE PRESENCE
    """

    # --------------------------------------------------
    # 1. COMMAND INPUT
    # --------------------------------------------------
    ride_id = command["ride_id"]

    # --------------------------------------------------
    # 2. LOAD AGGREGATE (REPLAY)
    # --------------------------------------------------
    agg = load_aggregate(store, ride_id)

    if agg.state is None:
        raise Exception("Ride does not exist")

    # --------------------------------------------------
    # 3. LOAD EVENT HISTORY
    # --------------------------------------------------
    events = store.load(ride_id)

    # --------------------------------------------------
    # 4. EXTRACT PICKUP LOCATION
    # --------------------------------------------------
    pickup = None

    for event in events:
        if event.type == "RideRequested":
            pickup = event.payload["pickup"]
            break

    if pickup is None:
        raise Exception("Missing pickup location")

    # --------------------------------------------------
    # 5. FETCH NEARBY DRIVERS
    # --------------------------------------------------
    nearby_drivers = geo_index.find_nearby(
        pickup=pickup,
        radius=command.get("radius"),
    )

    if not nearby_drivers:
        raise Exception("No nearby drivers")

    # --------------------------------------------------
    # 6. FILTER AVAILABLE DRIVERS
    # --------------------------------------------------
    available_drivers = [
        d for d in nearby_drivers
        if presence_service.is_available(d["id"])
    ]

    if not available_drivers:
        raise Exception("No available drivers")

    # --------------------------------------------------
    # 7. DETERMINISTIC MATCHING
    # --------------------------------------------------
    driver = match_driver(
        available_drivers,
        pickup
    )

    if not driver:
        raise Exception("Matching failed")

    # --------------------------------------------------
    # 8. AGGREGATE VALIDATION (SOURCE OF TRUTH)
    # --------------------------------------------------
    event = agg.assign_driver(
        ride_id=ride_id,
        driver_id=driver["id"]
    )

    # --------------------------------------------------
    # 9. PERSIST EVENT (OPTIMISTIC CONCURRENCY)
    # --------------------------------------------------
    store.append(
        stream_id=ride_id,
        expected_version=agg.version - 1,
        event=event,
    )

    # --------------------------------------------------
    # 10. UPDATE DRIVER PRESENCE STATE
    # --------------------------------------------------
    presence_service.set_busy(driver["id"])

    # --------------------------------------------------
    # ✅ 11. RETURN EVENT (CORRECT CONTRACT)
    # --------------------------------------------------
    return event