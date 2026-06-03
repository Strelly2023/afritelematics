from math import asin, cos, radians, sin, sqrt

from .models import LocationEvidence


MAX_SPEED_KH = 180
MAX_DISTANCE_JUMP_KM = 5
MAX_INTERVAL_SECONDS = 60


def haversine_km(first, second):
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


def detect_location_anomalies(ride_id):
    """Detect GPS evidence anomalies without mutating canonical ride state."""

    points = list(
        LocationEvidence.objects.filter(ride_id=ride_id).order_by("recorded_at", "id")
    )
    anomalies = []

    for index, point in enumerate(points):
        if point.speed and point.speed > MAX_SPEED_KH:
            anomalies.append(
                {
                    "point_id": point.id,
                    "type": "impossible_speed",
                    "value": point.speed,
                }
            )

        if index == 0:
            continue

        previous = points[index - 1]
        interval = (point.recorded_at - previous.recorded_at).total_seconds()
        distance_km = haversine_km(previous, point)

        if interval > MAX_INTERVAL_SECONDS:
            anomalies.append(
                {
                    "point_id": point.id,
                    "type": "missing_evidence_interval",
                    "interval_seconds": interval,
                }
            )

        if interval <= 5 and distance_km > MAX_DISTANCE_JUMP_KM:
            anomalies.append(
                {
                    "point_id": point.id,
                    "type": "gps_jump",
                    "distance_km": round(distance_km, 3),
                    "interval_seconds": interval,
                }
            )

    return {
        "anomaly_detected": bool(anomalies),
        "anomalies": anomalies,
    }
