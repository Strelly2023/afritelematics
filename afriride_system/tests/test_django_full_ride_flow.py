from __future__ import annotations

from uuid import uuid4

from afriride_system.django_app.apps.driver.models import Driver
from afriride_system.django_app.apps.ride_lifecycle.domain.entities import RideState
from afriride_system.django_app.apps.ride_lifecycle.services.lifecycle_service import (
    RideLifecycleService,
)
from afriride_system.django_app.apps.ride_matching.services.matching_service import (
    MatchingService,
)
from afriride_system.django_app.apps.ride_request.models import RideIntent
from afriride_system.django_app.apps.ride_request.services.ride_request_service import (
    RideRequestService,
)


def test_full_ride_flow() -> None:
    RideIntent.objects.clear()
    Driver.objects.clear()

    data = {
        "rider_id": uuid4(),
        "origin": {"label": "Melbourne CBD"},
        "destination": {"label": "Melbourne Airport"},
    }
    Driver.objects.create(name="Driver 001", is_available=True)

    ride, receipt = RideRequestService.create_ride_intent(data)
    driver = MatchingService.assign_driver()

    RideLifecycleService.transition(ride, RideState.MATCHED)
    RideLifecycleService.transition(ride, RideState.ACCEPTED)
    RideLifecycleService.transition(ride, RideState.STARTED)
    RideLifecycleService.transition(ride, RideState.COMPLETED)

    assert driver is not None
    assert ride.status == RideState.COMPLETED
    assert receipt.authority == "non_authoritative"
