from __future__ import annotations

from uuid import UUID

from rest_framework.decorators import api_view
from rest_framework.response import Response

from afritech.models import EventRecord, EvidenceBundle
from afritech.trust_kernel.consensus import consensus_state_hash, event_finality
from afritech.trust_kernel.projections import get_subject_projection, projection_hash
from afritech.trust_kernel.replay.engine import _verify_event_hash
from afritech.trust_kernel.signatures import stored_event_signature_verified
from afritech.trust_kernel.witness import required_witness_count, valid_witnesses


@api_view(["GET"])
def verify_event_view(request, event_id: UUID) -> Response:
    event = EventRecord.objects.filter(event_id=event_id).first()
    if event is None:
        return Response({"valid": False, "detail": "event not found"}, status=404)

    hash_valid = _event_hash_valid(event)
    witnesses = valid_witnesses(event)
    required_witnesses = required_witness_count(event.event_type)
    bundle = EvidenceBundle.objects.filter(event=event).first()

    return Response(
        {
            "valid": hash_valid and len(witnesses) >= required_witnesses,
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "event_hash": event.event_hash,
            "state_hash": projection_hash(),
            "subject_projection": get_subject_projection(event.subject_id),
            "signature": event.signature,
            "signature_verified": stored_event_signature_verified(event),
            "witnesses_required": required_witnesses,
            "witnesses": [
                {
                    "verifier_node": witness.verifier_node,
                    "signature": witness.signature,
                }
                for witness in witnesses
            ],
            "evidence_bundle_hash": bundle.bundle_hash if bundle else None,
            "evidence_bundle_root": (
                bundle.receipts.get("bundle_root") if bundle else None
            ),
            "consensus": consensus_state_hash(),
            "finality": event_finality(event),
        }
    )


def _event_hash_valid(event: EventRecord) -> bool:
    try:
        _verify_event_hash(event)
    except ValueError:
        return False
    return True
