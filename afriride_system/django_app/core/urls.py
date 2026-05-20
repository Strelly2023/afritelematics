"""URL declarations for the isolated AfriRide Django skeleton."""

from __future__ import annotations

try:
    from django.urls import include, path
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    urlpatterns: list[object] = []
else:
    urlpatterns = [
        path("api/v1/ride/", include("afriride_system.django_app.api.v1.ride.urls")),
    ]
