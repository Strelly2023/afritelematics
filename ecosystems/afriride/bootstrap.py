from ecosystems.core.infrastructure.persistence.event_store import EventStore

from ecosystems.afriride.core.infrastructure.streaming.redis_event_bus import (
    RedisEventBus,
)
from ecosystems.afriride.core.projections.projection_bus import ProjectionBus

from ecosystems.afriride.core.projections.ride_projection import RideProjection
from ecosystems.afriride.core.projections.driver_projection import DriverProjection
from ecosystems.afriride.core.projections.dispatch_projection import DispatchProjection

from ecosystems.afriride.core.projections.persistence.redis_projection_store import (
    RedisProjectionStore,
)


def build_system(
    use_event_streaming: bool = True,
    redis_url: str = "redis://localhost:6379/0",
):
    """
    Build AfriRide system (fully wired).

    Modes:
    - use_event_streaming = False → synchronous (ProjectionBus only)
    - use_event_streaming = True  → async (Redis Streams + workers)

    Returns:
    - store (EventStore)
    - projections
    - projection_bus (for sync / replay)
    - event_bus (if async enabled)
    """

    # --------------------------------------------------
    # 1. EVENT BUS (ASYNC LAYER)
    # --------------------------------------------------
    event_bus = None
    if use_event_streaming:
        event_bus = RedisEventBus(url=redis_url)

    # --------------------------------------------------
    # 2. EVENT STORE
    # --------------------------------------------------
    store = EventStore(event_bus=event_bus)

    # --------------------------------------------------
    # 3. PROJECTION STORE (REDIS)
    # --------------------------------------------------
    redis_store = RedisProjectionStore(redis_url)

    # --------------------------------------------------
    # 4. PROJECTIONS (READ MODELS)
    # --------------------------------------------------
    ride_projection = RideProjection(redis_store)
    driver_projection = DriverProjection(redis_store)
    dispatch_projection = DispatchProjection(redis_store)

    projections = [
        ride_projection,
        driver_projection,
        dispatch_projection,
    ]

    # --------------------------------------------------
    # 5. PROJECTION BUS (SYNC MODE + REPLAY SUPPORT)
    # --------------------------------------------------
    projection_bus = ProjectionBus(projections)

    # --------------------------------------------------
    # 6. CONNECT MODE
    # --------------------------------------------------
    if use_event_streaming:
        # Async mode: projections handled by workers
        store.set_event_bus(event_bus)
    else:
        # Sync mode: projections updated inline
        store.set_projection_bus(projection_bus)

    # --------------------------------------------------
    # 7. RETURN SYSTEM
    # --------------------------------------------------
    return {
        "store": store,
        "event_bus": event_bus,
        "projection_bus": projection_bus,
        "ride_projection": ride_projection,
        "driver_projection": driver_projection,
        "dispatch_projection": dispatch_projection,
    }