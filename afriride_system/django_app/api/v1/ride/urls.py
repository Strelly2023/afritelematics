"""Ride API URL declarations."""

from __future__ import annotations

try:
    from django.urls import path
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    urlpatterns: list[object] = []
else:
    from afriride_system.django_app.api.v1.ride.views import CreateRideView

    urlpatterns = [
        path("request/", CreateRideView.as_view()),
    ]
