import hashlib
import json

from rides.models import Ride
from replay.services import generate_replay_receipt


COMPLETED_STATUS = "completed"


def canonical_report_hash(payload):
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_transport_activity_report(country, start_date, end_date):
    rides = Ride.objects.filter(
        country=country,
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    verified = []

    for ride in rides:
        receipt = generate_replay_receipt(ride.id)
        verified_state = receipt.get("verified_state", {})

        if verified_state.get("status") == COMPLETED_STATUS:
            verified.append(
                {
                    "ride_id": ride.id,
                    "rider_id": ride.rider_id,
                    "driver_id": ride.driver_id,
                    "completed": True,
                    "replay_receipt_id": receipt.get("receipt_id"),
                }
            )

    payload = {
        "authority": "replay_backed_regulatory_report",
        "country": country,
        "period_start": str(start_date),
        "period_end": str(end_date),
        "completed_rides": verified,
        "ride_count": len(verified),
    }

    return payload, canonical_report_hash(payload)
