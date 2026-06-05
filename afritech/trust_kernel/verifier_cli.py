from __future__ import annotations

import argparse
import json

from afritech.models import EventRecord
from afritech.trust_kernel.consensus import event_finality
from afritech.trust_kernel.projections import get_subject_projection, projection_hash
from afritech.trust_kernel.replay.engine import _verify_event_hash
from afritech.trust_kernel.signatures import stored_event_signature_verified
from afritech.trust_kernel.witness import required_witness_count, valid_witnesses


def verify_event(event_id: str) -> dict[str, object]:
    event = EventRecord.objects.get(event_id=event_id)
    hash_valid = _hash_valid(event)
    witnesses = valid_witnesses(event)
    witness_count = len(witnesses)
    required = required_witness_count(event.event_type)
    return {
        "valid": hash_valid and witness_count >= required,
        "event_id": str(event.event_id),
        "event_hash": event.event_hash,
        "event_type": event.event_type,
        "signature_verified": stored_event_signature_verified(event),
        "witness_count": witness_count,
        "witnesses_required": required,
        "state_hash": projection_hash(),
        "subject_projection": get_subject_projection(event.subject_id),
        "finality": event_finality(event),
    }


def main() -> None:
    parser = argparse.ArgumentParser("AfriTech external verifier")
    parser.add_argument("event_id")
    args = parser.parse_args()
    print(json.dumps(verify_event(args.event_id), indent=2, sort_keys=True))


def _hash_valid(event: EventRecord) -> bool:
    try:
        _verify_event_hash(event)
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    main()
