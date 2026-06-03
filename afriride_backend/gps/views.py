from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from rides.models import Ride

from .serializers import GPSUpdateSerializer
from .services import store_location, verify_location_chain


class GPSUpdateView(APIView):
    """Store driver GPS evidence for an active ride.

    This endpoint records GPS facts. It does not complete rides, certify routes,
    or move replay authority into the mobile client.
    """

    def post(self, request):
        serializer = GPSUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        ride = Ride.objects.get(id=data["ride_id"])
        point = store_location(
            ride=ride,
            latitude=data["latitude"],
            longitude=data["longitude"],
            speed=data.get("speed", 0),
            heading=data.get("heading", 0),
            timestamp=data.get("recorded_at") or timezone.now(),
        )
        chain_status = verify_location_chain(ride_id=ride.id)

        return Response(
            {
                "status": "stored",
                "authority": "gps_evidence_only",
                "ride_id": ride.id,
                "point_id": point.id,
                "event_hash": point.event_hash,
                "chain_verified": chain_status["verified"],
            },
            status=status.HTTP_201_CREATED,
        )
