"""Composition root for the AfriRide Phase 1 interface system."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from afriride_system.backend.repositories import (
    DriverRepository,
    EventRepository,
    IdempotencyRepository,
    RideRepository,
)
from afriride_system.backend.storage import AfriRideStorage, DEFAULT_DB_PATH
from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRideCommandDispatcher,
)
from afriride_system.backend.command_api.driver_routes import DriverRoutes
from afriride_system.backend.command_api.passenger_routes import PassengerRoutes
from afriride_system.backend.query_api.read_model import AfriRideReadModel
from afriride_system.integration.websocket_gateway.event_bridge import EventBridge


@dataclass(frozen=True)
class AfriRideGateway:
    storage: AfriRideStorage
    idempotency_repository: IdempotencyRepository
    event_bridge: EventBridge
    dispatcher: AfriRideCommandDispatcher
    passenger: PassengerRoutes
    driver: DriverRoutes
    read_model: AfriRideReadModel


def build_gateway(
    *,
    db_path: str | Path | None = None,
    reset: bool = False,
) -> AfriRideGateway:
    storage = AfriRideStorage(db_path or DEFAULT_DB_PATH)
    if reset:
        storage.reset()

    driver_repository = DriverRepository(storage)
    ride_repository = RideRepository(storage)
    event_repository = EventRepository(storage)
    idempotency_repository = IdempotencyRepository(storage)
    event_bridge = EventBridge()
    dispatcher = AfriRideCommandDispatcher(
        event_bridge=event_bridge,
        driver_repository=driver_repository,
        ride_repository=ride_repository,
        event_repository=event_repository,
    )
    return AfriRideGateway(
        storage=storage,
        idempotency_repository=idempotency_repository,
        event_bridge=event_bridge,
        dispatcher=dispatcher,
        passenger=PassengerRoutes(dispatcher),
        driver=DriverRoutes(dispatcher),
        read_model=AfriRideReadModel(dispatcher),
    )
