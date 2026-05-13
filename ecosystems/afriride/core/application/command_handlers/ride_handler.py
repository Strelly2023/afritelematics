from ecosystems.core.infrastructure.persistence.event_store import EventStore

from ecosystems.afriride.core.application.command_handlers.request_ride_handler import (
    handle_request_ride,
)
from ecosystems.afriride.core.application.command_handlers.accept_driver_handler import (
    handle_accept_driver,
)
from ecosystems.afriride.core.application.command_handlers.assign_driver_handler import (
    handle_assign_driver,
)
from ecosystems.afriride.core.application.command_handlers.start_trip_handler import (
    handle_start_trip,
)
from ecosystems.afriride.core.application.command_handlers.complete_trip_handler import (
    handle_complete_trip,
)
from ecosystems.afriride.core.application.command_handlers.cancel_trip_handler import (
    handle_cancel_trip,
)


class RideHandler:
    """
    Unified command façade for ride operations.

    Responsibilities:
    - Central entry point for all ride commands
    - Delegates to specific command handlers
    - Keeps adapters (API/CLI) simple
    - Does NOT contain business logic
    """

    def __init__(self, store: EventStore):
        self.store = store

    # --------------------------------------------------
    # CREATE RIDE
    # --------------------------------------------------
    def request(self, command: dict):
        return handle_request_ride(command, self.store)

    # --------------------------------------------------
    # DRIVER ACCEPTS OFFER
    # --------------------------------------------------
    def accept_driver(self, command: dict):
        return handle_accept_driver(command, self.store)

    # --------------------------------------------------
    # ASSIGN DRIVER (manual or dispatch)
    # --------------------------------------------------
    def assign_driver(self, command: dict):
        return handle_assign_driver(command, self.store)

    # --------------------------------------------------
    # START TRIP
    # --------------------------------------------------
    def start_trip(self, command: dict):
        return handle_start_trip(command, self.store)

    # --------------------------------------------------
    # COMPLETE TRIP
    # --------------------------------------------------
    def complete_trip(self, command: dict):
        return handle_complete_trip(command, self.store)

    # --------------------------------------------------
    # CANCEL TRIP
    # --------------------------------------------------
    def cancel_trip(self, command: dict):
        return handle_cancel_trip(command, self.store)
