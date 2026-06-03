import hashlib
from datetime import timezone as datetime_timezone

from django.utils import timezone

from .models import LocationEvidence


_HASH_SEPARATOR = "|"


_DECIMAL_PLACES = 6


def normalize_coordinate(value):
    return f"{float(value):.{_DECIMAL_PLACES}f}"


def normalize_timestamp(value):
    return value.astimezone(datetime_timezone.utc).isoformat().replace("+00:00", "Z")


def build_canonical_location_payload(previous_hash, latitude, longitude, recorded_at):
    return _HASH_SEPARATOR.join(
        [
            previous_hash or "",
            normalize_coordinate(latitude),
            normalize_coordinate(longitude),
            normalize_timestamp(recorded_at),
        ]
    )


def compute_location_hash(previous_hash, latitude, longitude, recorded_at):
    payload = build_canonical_location_payload(
        previous_hash=previous_hash,
        latitude=latitude,
        longitude=longitude,
        recorded_at=recorded_at,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def get_previous_location(ride):
    return (
        LocationEvidence.objects.filter(ride=ride)
        .order_by("-recorded_at", "-id")
        .first()
    )


def store_location(ride, latitude, longitude, speed=0, heading=0, timestamp=None):
    """Append a GPS point to the immutable location evidence chain."""

    recorded_at = timestamp or timezone.now()
    previous_location = get_previous_location(ride)
    previous_hash = previous_location.event_hash if previous_location else ""
    event_hash = compute_location_hash(
        previous_hash=previous_hash,
        latitude=latitude,
        longitude=longitude,
        recorded_at=recorded_at,
    )

    return LocationEvidence.objects.create(
        ride=ride,
        latitude=latitude,
        longitude=longitude,
        speed=speed or 0,
        heading=heading or 0,
        recorded_at=recorded_at,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )


def verify_location_chain(ride_id):
    """Verify the GPS evidence hash chain for a ride."""

    previous_hash = ""
    for point in LocationEvidence.objects.filter(ride_id=ride_id).order_by(
        "recorded_at", "id"
    ):
        expected_hash = compute_location_hash(
            previous_hash=previous_hash,
            latitude=point.latitude,
            longitude=point.longitude,
            recorded_at=point.recorded_at,
        )
        if point.previous_hash != previous_hash or point.event_hash != expected_hash:
            return {
                "verified": False,
                "failed_point_id": point.id,
                "reason": "gps_hash_chain_mismatch",
            }
        previous_hash = point.event_hash

    return {
        "verified": True,
        "failed_point_id": None,
        "reason": None,
    }
