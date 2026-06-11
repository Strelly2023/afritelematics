from __future__ import annotations

import uuid
from typing import Any, Dict, List

from django.db import transaction

from afritech.models import (
    EventRecord,
    EvidenceBundle,
    LedgerRootLog,
    WitnessSignature,
)
from afritech.trust_kernel.hashing import event_hash, sha256_payload
from afritech.trust_kernel.policy import Command, guard_event_integrity
from afritech.trust_kernel.signatures import SIGNATURE_MODE_ED25519


# ------------------------------------------------------------------------------------
# COMMAND ENTRY POINTS
# ------------------------------------------------------------------------------------

def process_command(command: Command) -> EventRecord:
    """Process a trusted internal command."""
    guard_event_integrity(command)

    event = append_event(command)
    emit_receipts(event, command)
    append_ledger_root()

    return event


def process_client_command(command: Command) -> EventRecord:
    """Process a client-signed command (strict signature requirement)."""
    if command.signature.get("signature_mode") != SIGNATURE_MODE_ED25519:
        raise ValueError("CLIENT_SIGNED_EVENT_REQUIRED")

    guard_event_integrity(command)

    event = append_event(command)
    emit_receipts(event, command)
    append_ledger_root()

    return event


# ------------------------------------------------------------------------------------
# EVENT APPEND (CHAIN CONSISTENCY)
# ------------------------------------------------------------------------------------

@transaction.atomic
def append_event(command: Command) -> EventRecord:
    """Append event to event chain with deterministic hashing."""

    last = EventRecord.objects.order_by("-created_at", "-event_id").first()
    prev_hash = last.event_hash if last else "GENESIS"

    event_id = uuid.uuid4()

    computed_hash = event_hash(
        event_id=str(event_id),
        event_type=command.event_type,
        actor_id=command.actor_id,
        subject_id=command.subject_id,
        prev_hash=prev_hash,
        payload=command.payload,
        signature=command.signature,
    )

    event = EventRecord.objects.create(
        event_id=event_id,
        event_type=command.event_type,
        actor_id=command.actor_id,
        subject_id=command.subject_id,
        prev_hash=prev_hash,
        event_hash=computed_hash,
        payload=command.payload,
        signature=command.signature,
    )

    return event


# ------------------------------------------------------------------------------------
# RECEIPTS / EVIDENCE
# ------------------------------------------------------------------------------------

def emit_receipts(event: EventRecord, command: Command) -> EvidenceBundle:
    """Emit deterministic evidence bundle for event."""

    witness_rows: List[Dict[str, str]] = []

    for witness in getattr(command, "witnesses", []) or []:
        row = WitnessSignature.objects.create(
            event=event,
            verifier_node=str(witness.get("verifier_node", "")),
            signature=str(witness.get("signature", "")),
        )

        witness_rows.append(
            {
                "verifier_node": row.verifier_node,
                "signature": row.signature,
            }
        )

    receipts: Dict[str, Any] = {
        "event_id": str(event.event_id),
        "event_type": event.event_type,
        "event_hash": event.event_hash,
        "prev_hash": event.prev_hash,
    }

    bundle_root = evidence_bundle_root(
        event_hash_value=event.event_hash,
        receipts=receipts,
        witnesses=witness_rows,
    )

    bundle_hash = sha256_payload(
        {
            "receipts": receipts,
            "witnesses": witness_rows,
            "bundle_root": bundle_root,
        }
    )

    return EvidenceBundle.objects.create(
        event=event,
        receipts={**receipts, "bundle_root": bundle_root},
        witnesses=witness_rows,
        bundle_hash=bundle_hash,
    )


# ------------------------------------------------------------------------------------
# METRICS / COUNTERS
# ------------------------------------------------------------------------------------

def event_count() -> int:
    """Return current number of events in ledger."""
    return EventRecord.objects.count()


# ------------------------------------------------------------------------------------
# HASHING UTILITIES
# ------------------------------------------------------------------------------------

def evidence_bundle_root(
    *,
    event_hash_value: str,
    receipts: Dict[str, Any],
    witnesses: List[Dict[str, Any]],
) -> str:
    """Compute deterministic root for evidence bundle."""
    return sha256_payload(
        {
            "event_hash": event_hash_value,
            "receipts": receipts,
            "witnesses": witnesses,
        }
    )


# ------------------------------------------------------------------------------------
# LEDGER ROOT MAINTENANCE
# ------------------------------------------------------------------------------------

def append_ledger_root() -> LedgerRootLog:
    """Append or reuse ledger root (deterministic chain summary)."""

    events = list(EventRecord.objects.order_by("created_at", "event_id"))

    root_hash = sha256_payload([event.event_hash for event in events])
    latest = events[-1].event_hash if events else ""

    existing = LedgerRootLog.objects.filter(root_hash=root_hash).first()
    if existing is not None:
        return existing

    return LedgerRootLog.objects.create(
        root_hash=root_hash,
        event_count=len(events),
        latest_event_hash=latest,
    )
