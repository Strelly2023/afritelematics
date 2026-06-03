from math import asin, cos, radians, sin, sqrt

from gps.models import LocationEvidence


def _haversine_km(first, second):
    lat1 = radians(float(first.latitude))
    lng1 = radians(float(first.longitude))
    lat2 = radians(float(second.latitude))
    lng2 = radians(float(second.longitude))

    delta_lat = lat2 - lat1
    delta_lng = lng2 - lng1

    value = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lng / 2) ** 2
    )
    return 6371 * 2 * asin(sqrt(value))


class RouteReplayEngine:
    """Reconstruct an observed route from immutable GPS evidence."""

    def __init__(self, ride_id):
        self.ride_id = ride_id
        self.points = LocationEvidence.objects.filter(ride_id=ride_id).order_by(
            "recorded_at", "id"
        )

    def reconstruct_route(self):
        return [
            {
                "lat": float(point.latitude),
                "lng": float(point.longitude),
                "time": point.recorded_at.isoformat(),
                "speed": point.speed,
                "heading": point.heading,
                "event_hash": point.event_hash,
            }
            for point in self.points
        ]

    def distance_km(self):
        points = list(self.points)
        if len(points) < 2:
            return 0
        return round(
            sum(
                _haversine_km(points[index - 1], points[index])
                for index in range(1, len(points))
            ),
            3,
        )

    def duration_minutes(self):
        points = list(self.points)
        if len(points) < 2:
            return 0
        seconds = (points[-1].recorded_at - points[0].recorded_at).total_seconds()
        return round(seconds / 60, 2)
