"""Service layer for creating ride intents."""

from __future__ import annotations

from typing import Any

from afriride_system.django_app.apps.ride_request.models import RideIntent
from afriride_system.django_app.apps.ride_request.validators.input_validator import (
    RideRequestValidator,
)
from afriride_system.django_app.orchestration.validation_bridge import (
    ValidationReceipt,
    validate_execution,
)


class RideRequestService:
    """Create ride intents without claiming constitutional authority."""

    @staticmethod
    def create_ride_intent(data: dict[str, Any]) -> tuple[RideIntent, ValidationReceipt]:
        RideRequestValidator.validate(data)
        ride = RideIntent.objects.create(
            rider_id=data["rider_id"],
            origin=data["origin"],
            destination=data["destination"],
        )
        receipt = validate_execution(ride)
        return ride, receipt
