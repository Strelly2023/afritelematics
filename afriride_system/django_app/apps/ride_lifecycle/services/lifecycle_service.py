"""Deterministic ride lifecycle transitions."""

from __future__ import annotations

from afriride_system.django_app.apps.ride_lifecycle.domain.entities import RideState
from afriride_system.django_app.apps.ride_request.models import RideIntent


class RideLifecycleService:
    """Apply deterministic ride state transitions."""

    @staticmethod
    def transition(ride: RideIntent, new_state: str) -> RideIntent:
        if new_state not in RideState.ORDER:
            raise ValueError("Invalid state")
        current_index = RideState.ORDER.index(ride.status)
        next_index = RideState.ORDER.index(new_state)
        if next_index < current_index:
            raise ValueError("State transition cannot move backward")
        ride.status = new_state
        return ride.save()
