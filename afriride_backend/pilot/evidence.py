import hashlib
import json

from replay.services import generate_replay_receipt

from .models import PilotEvidence


COMPLETED_STATUS = "completed"


def canonical_receipt_hash(receipt):
    payload = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def collect_ride_evidence(pilot, ride):
    replay_receipt = generate_replay_receipt(ride.id)
    verified_state = replay_receipt.get("verified_state", {})
    replay_verified = verified_state.get("status") == COMPLETED_STATUS
    receipt_hash = canonical_receipt_hash(replay_receipt)

    evidence, _ = PilotEvidence.objects.update_or_create(
        pilot=pilot,
        ride=ride,
        defaults={
            "replay_verified": replay_verified,
            "receipt_hash": receipt_hash,
        },
    )

    return evidence


def pilot_evidence_summary(pilot):
    records = PilotEvidence.objects.filter(pilot=pilot)
    total = records.count()
    verified = records.filter(replay_verified=True).count()
    return {
        "pilot_id": pilot.id,
        "total_evidence_records": total,
        "replay_verified_records": verified,
        "replay_verification_rate": round((verified / total) * 100, 2) if total else 0,
    }
