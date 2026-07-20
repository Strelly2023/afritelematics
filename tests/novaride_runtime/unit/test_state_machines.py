from __future__ import annotations

import pytest

from afritech.novaride_runtime.common.errors import InvalidTransition
from afritech.novaride_runtime.models import ActorType, BookingState, EmergencyState, TripState
from afritech.novaride_runtime.state_machines import transition_rule


def test_booking_trip_and_emergency_transitions_are_explicit() -> None:
    booking = transition_rule(BookingState.QUOTED, BookingState.CONFIRMED, ActorType.RIDER)
    trip = transition_rule(TripState.DRIVER_ARRIVED, TripState.PICKUP_VERIFIED, ActorType.DRIVER)
    emergency = transition_rule(
        EmergencyState.TRIGGERED, EmergencyState.ACKNOWLEDGED, ActorType.OPERATOR
    )

    assert booking.emitted_events == ("BookingConfirmed",)
    assert "pickup_pin_or_qr" in trip.required_evidence
    assert emergency.authority == "OPERATOR"


def test_invalid_transition_rejected() -> None:
    with pytest.raises(InvalidTransition):
        transition_rule(TripState.CREATED, TripState.COMPLETED, ActorType.NOVAAI)
