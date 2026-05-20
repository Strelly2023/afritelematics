"""Composition root for the AfriRide Phase 1 interface system."""

from __future__ import annotations

from dataclasses import dataclass

from afriride_system.backend.command_api.command_dispatcher_adapter import (
    AfriRideCommandDispatcher,
)
from afriride_system.backend.command_api.driver_routes import DriverRoutes
from afriride_system.backend.command_api.passenger_routes import PassengerRoutes
from afriride_system.backend.query_api.read_model import AfriRideReadModel
from afriride_system.integration.websocket_gateway.event_bridge import EventBridge


@dataclass(frozen=True)
class AfriRideGateway:
    event_bridge: EventBridge
    dispatcher: AfriRideCommandDispatcher
    passenger: PassengerRoutes
    driver: DriverRoutes
    read_model: AfriRideReadModel


def build_gateway() -> AfriRideGateway:
    event_bridge = EventBridge()
    dispatcher = AfriRideCommandDispatcher(event_bridge=event_bridge)
    return AfriRideGateway(
        event_bridge=event_bridge,
        dispatcher=dispatcher,
        passenger=PassengerRoutes(dispatcher),
        driver=DriverRoutes(dispatcher),
        read_model=AfriRideReadModel(dispatcher),
    )
