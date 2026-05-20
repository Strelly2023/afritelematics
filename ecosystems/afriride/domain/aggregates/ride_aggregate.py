from ecosystems.afriride.domain.state.ride_state import RideStatus
from ecosystems.afriride.domain.events.ride_events import (
    RideRequested,
    DriverAssigned,
    TripStarted,
    TripCompleted,
    TripCancelled,
)


class RideAggregate:
    """
    Canonical event-sourced aggregate.

    Guarantees:
    - Events are the single source of truth
    - apply() is a deterministic reducer
    - Commands enforce intent invariants
    - Aggregate enforces transition invariants only
    """

    def __init__(self):
        self.state: RideStatus | None = None
        self.version: int = 0
        self.ride_id: str | None = None

    # --------------------------------------------------
    # TRANSITION INVARIANT (LOCAL ONLY)
    # --------------------------------------------------
    def _ensure_can_transition(self, target):

        allowed = {
            None: {RideStatus.REQUESTED},
            RideStatus.REQUESTED: {RideStatus.ASSIGNED, RideStatus.COMPLETED},  # allow cancel → completed
            RideStatus.ASSIGNED: {RideStatus.IN_PROGRESS, RideStatus.COMPLETED},
            RideStatus.IN_PROGRESS: {RideStatus.COMPLETED},
            RideStatus.COMPLETED: set(),
        }

        if target not in allowed.get(self.state, set()):
            raise Exception(
                f"Invalid transition {self.state} → {target}"
            )

    # --------------------------------------------------
    # APPLY (DETERMINISTIC REDUCER)
    # --------------------------------------------------
    def apply(self, event):

        if event.type == "RideRequested":

            self._ensure_can_transition(RideStatus.REQUESTED)

            self.ride_id = event.payload["ride_id"]
            self.state = RideStatus.REQUESTED

        elif event.type == "DriverAssigned":

            self._validate_identity(event)
            self._ensure_can_transition(RideStatus.ASSIGNED)

            self.state = RideStatus.ASSIGNED

        elif event.type == "TripStarted":

            self._validate_identity(event)
            self._ensure_can_transition(RideStatus.IN_PROGRESS)

            self.state = RideStatus.IN_PROGRESS

        elif event.type == "TripCompleted":

            self._validate_identity(event)
            self._ensure_can_transition(RideStatus.COMPLETED)

            self.state = RideStatus.COMPLETED

        # --------------------------------------------------
        # NEW: TRIP CANCELLED
        # treated as terminal state (mapped to COMPLETED)
        # --------------------------------------------------
        elif event.type == "TripCancelled":

            self._validate_identity(event)
            self._ensure_can_transition(RideStatus.COMPLETED)

            self.state = RideStatus.COMPLETED

        # --------------------------------------------------
        # ORCHESTRATION EVENTS (NO STATE CHANGE)
        # --------------------------------------------------
        elif event.type in (
            "DriverOffered",
            "OfferExpired",
            "DriverAccepted",
        ):
            pass

        else:
            raise Exception(f"Unknown event type: {event.type}")

        # version = event count
        self.version += 1

    # --------------------------------------------------
    # REPLAY
    # --------------------------------------------------
    def apply_all(self, events):
        for event in events:
            self.apply(event)

    # --------------------------------------------------
    # COMMANDS (INTENT VALIDATION ONLY)
    # --------------------------------------------------
    def request_ride(self, ride_id, rider_id, pickup, dropoff):

        if self.state is not None:
            raise Exception("Ride already exists")

        event = RideRequested(
            ride_id=ride_id,
            rider_id=rider_id,
            pickup=pickup,
            dropoff=dropoff,
        )

        self.apply(event)
        return event

    def assign_driver(self, ride_id, driver_id):

        self._ensure_exists()
        self._ensure_not_terminal()
        self._validate_identity_payload(ride_id)

        event = DriverAssigned(
            ride_id=ride_id,
            driver_id=driver_id,
        )

        self.apply(event)
        return event

    def start_trip(self, ride_id):

        self._ensure_exists()
        self._validate_identity_payload(ride_id)
        self._ensure_not_terminal()

        event = TripStarted(ride_id)

        self.apply(event)
        return event

    def complete_trip(self, ride_id):

        self._ensure_exists()
        self._validate_identity_payload(ride_id)

        event = TripCompleted(ride_id)

        self.apply(event)
        return event

    # --------------------------------------------------
    # OPTIONAL COMMAND (NOW COMPLETE)
    # --------------------------------------------------
    def cancel_trip(self, ride_id, reason=None):

        self._ensure_exists()
        self._validate_identity_payload(ride_id)
        self._ensure_not_terminal()

        event = TripCancelled(
            ride_id=ride_id,
            reason=reason,
        )

        self.apply(event)
        return event

    # --------------------------------------------------
    # INVARIANTS
    # --------------------------------------------------
    def _validate_identity(self, event):
        if self.ride_id != event.payload["ride_id"]:
            raise Exception("Ride ID mismatch")

    def _validate_identity_payload(self, ride_id):
        if self.ride_id != ride_id:
            raise Exception("Ride ID mismatch")

    def _ensure_exists(self):
        if self.state is None:
            raise Exception("Ride not initialized")

    def _ensure_not_terminal(self):
        if self.state == RideStatus.COMPLETED:
            raise Exception("Ride already completed")

    # --------------------------------------------------
    # DEBUG / PROJECTION SUPPORT
    # --------------------------------------------------
    def snapshot(self):
        return {
            "ride_id": self.ride_id,
            "state": self.state.value if self.state else None,
            "version": self.version,
        }