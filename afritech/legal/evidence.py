from __future__ import annotations

from afritech.models import EventRecord, EvidenceBundle, LegalEvidenceExport
from afritech.trust_kernel.hashing import sha256_payload
from afritech.trust_kernel.projections import projection_hash
from afritech.trust_kernel.signatures import stored_event_signature_verified
from afritech.trust_kernel.witness import valid_witnesses


class LegalEvidenceError(ValueError):
    """Raised when legal export lacks replayable evidence."""


def export_legal_evidence_bundle(
    *,
    event_id: str,
    jurisdiction: str,
    compliance_tags: tuple[str, ...],
) -> LegalEvidenceExport:
    event = EventRecord.objects.get(event_id=event_id)
    bundle = EvidenceBundle.objects.filter(event=event).first()
    if bundle is None:
        raise LegalEvidenceError("legal export requires evidence bundle")
    signatures = _signatures_for_event(event)
    if not signatures:
        raise LegalEvidenceError("legal export requires verifiable signatures or witnesses")
    replay_state_hash = projection_hash()
    export_hash = sha256_payload(
        {
            "event_id": str(event.event_id),
            "event_hash": event.event_hash,
            "bundle_hash": bundle.bundle_hash,
            "jurisdiction": jurisdiction,
            "compliance_tags": list(compliance_tags),
            "replay_state_hash": replay_state_hash,
            "signatures": signatures,
        }
    )
    record, _ = LegalEvidenceExport.objects.update_or_create(
        export_hash=export_hash,
        defaults={
            "event": event,
            "evidence_bundle": bundle,
            "jurisdiction": jurisdiction,
            "compliance_tags": list(compliance_tags),
            "replay_state_hash": replay_state_hash,
            "signatures": signatures,
        },
    )
    return record


def _signatures_for_event(event: EventRecord) -> list[dict[str, str]]:
    signatures: list[dict[str, str]] = []
    if stored_event_signature_verified(event):
        signatures.append(
            {
                "type": "actor_signature",
                "actor_id": event.actor_id,
                "signature": str(event.signature.get("signature")),
            }
        )
    for witness in valid_witnesses(event):
        signatures.append(
            {
                "type": "witness_signature",
                "verifier_node": witness.verifier_node,
                "signature": witness.signature,
            }
        )
    return signatures
