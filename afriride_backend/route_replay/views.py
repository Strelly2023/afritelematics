from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_route_replay


class RouteReplayView(APIView):
    """Expose route replay as visual evidence projection."""

    def get(self, request, ride_id):
        return Response(get_route_replay(ride_id=ride_id))
