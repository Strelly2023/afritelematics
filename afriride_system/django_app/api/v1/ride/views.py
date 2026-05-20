"""Ride API views for the isolated AfriRide skeleton."""

from __future__ import annotations

from typing import Any

from afriride_system.django_app.apps.ride_request.services.ride_request_service import (
    RideRequestService,
)

try:
    from rest_framework.response import Response
    from rest_framework.views import APIView
except ModuleNotFoundError:  # pragma: no cover - dependency hook
    class Response(dict):  # type: ignore[no-redef]
        """Small fallback response for dependency-free tests."""

    class APIView:  # type: ignore[no-redef]
        """Small fallback APIView for dependency-free tests."""


class CreateRideView(APIView):
    """Create a ride intent through the product service layer."""

    def post(self, request: Any) -> Response:
        payload = getattr(request, "data", request)
        ride, receipt = RideRequestService.create_ride_intent(payload)
        return Response(
            {
                "ride_id": str(ride.id),
                "status": ride.status,
                "validation": {
                    "bridge": receipt.bridge,
                    "authority": receipt.authority,
                },
            }
        )
