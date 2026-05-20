from __future__ import annotations

from uuid import uuid4

from afriride_system.django_app.apps.ride_lifecycle.domain.entities import RideState
from afriride_system.django_app.apps.ride_lifecycle.services.lifecycle_service import (
    RideLifecycleService,
)
from afriride_system.django_app.apps.ride_request.models import RideIntent
from afriride_system.django_app.apps.ride_request.services.ride_request_service import (
    RideRequestService,
)
from afriride_system.django_app.apps.pricing.services.pricing_service import PricingService


def create_test_ride() -> RideIntent:
    data = {
        "rider_id": uuid4(),
        "origin": {"lat": 1, "lng": 1},
        "destination": {"lat": 2, "lng": 2},
    }
    ride, _receipt = RideRequestService.create_ride_intent(data)
    return ride


def test_create_ride() -> None:
    RideIntent.objects.clear()

    ride = create_test_ride()

    assert ride.status == RideState.REQUESTED


def test_lifecycle_transition() -> None:
    RideIntent.objects.clear()
    ride = create_test_ride()

    RideLifecycleService.transition(ride, RideState.MATCHED)

    assert ride.status == RideState.MATCHED


def test_pricing_deterministic() -> None:
    price1 = PricingService.calculate(10)
    price2 = PricingService.calculate(10)

    assert price1 == price2
