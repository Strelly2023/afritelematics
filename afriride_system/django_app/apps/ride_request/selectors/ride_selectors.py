"""Ride request selectors."""

from __future__ import annotations

from afriride_system.django_app.apps.ride_request.models import RideIntent


def list_ride_intents() -> tuple[RideIntent, ...]:
    return RideIntent.objects.all()
