"""Portable receipt derivation from persisted trace and replay."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from afriride_system.backend.authority_runtime import (
    DOC_VERSION,
    assert_consistent_authority_hashes,
    authority_envelope,
    execution_fingerprint,
)
from afriride_system.backend.evidence_engine import EvidenceEngine, EvidenceRecord
from afriride_system.backend.receipt_signing import (
    SIGNATURE_MODE,
    sign_receipt_hash,
    verify_receipt_signature,
)
from afriride_system.backend.replay_engine import ReplayEngine
from afriride_system.backend.trace_enforcement import TraceEvent

__doc_authority__ = "DOC-ARCH-001"
__doc_version__ = "1.0.0"
__governed_invariants__ = (
    "I3_NO_SILENT_MUTATION",
    "I4_DETERMINISTIC_EXECUTION",
    "I5_REPLAY_REQUIRED",
    "I6_REPLAY_AUTHORITY",
    "I7_TRANSCRIPT_COMPLETENESS",
    "I8_TRANSCRIPT_HASH_STABILITY",
    "I11_AUTHORITY_DECLARATION",
)


@dataclass(frozen=True)
class ReceiptSignature:
    signature_mode: str
    signature: str
    all_signatures_valid: bool

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "signature_mode": self.signature_mode,
            "signature": self.signature,
            "all_signatures_valid": self.all_signatures_valid,
        }


@dataclass(frozen=True)
class ReceiptRecord:
    ride_id: str
    receipt_id: str
    replay_id: str
    status: str
    trace_hash: str
    replay_hash: str
    receipt_hash: str
    execution_fingerprint: str
    issued_at: str
    signature_validation: ReceiptSignature

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "receipt_id": self.receipt_id,
            "status": self.status.lower(),
            "replay_id": self.replay_id,
            "trace_hash": self.trace_hash,
            "replay_hash": self.replay_hash,
            "receipt_hash": self.receipt_hash,
            "execution_fingerprint": self.execution_fingerprint,
            "issued_at": self.issued_at,
            "signature_validation": self.signature_validation.canonical_dict(),
            "authority": authority_envelope(
                doc_id=__doc_authority__,
                doc_version=__doc_version__,
                governed_invariants=__governed_invariants__,
                surface="receipt_record",
            ),
        }


class ReceiptEngine:
    def __init__(
        self,
        replay_engine: ReplayEngine | None = None,
        evidence_engine: EvidenceEngine | None = None,
    ) -> None:
        self.replay_engine = replay_engine or ReplayEngine()
        self.evidence_engine = evidence_engine or EvidenceEngine(self.replay_engine)

    def derive(self, ride_id: str, events: tuple[TraceEvent, ...]) -> ReceiptRecord:
        evidence = self.evidence_engine.derive(ride_id, events)
        receipt_authority = authority_envelope(
            doc_id=__doc_authority__,
            doc_version=__doc_version__,
            governed_invariants=__governed_invariants__,
            surface="receipt_record",
        )["authority_hash"]
        authority_hash = assert_consistent_authority_hashes(
            replay=evidence.replay.canonical_dict()["authority"]["authority_hash"],
            evidence=evidence.canonical_dict()["authority"]["authority_hash"],
            receipt=receipt_authority,
        )
        receipt_payload = _receipt_payload(evidence)
        receipt_hash = _stable_hash(receipt_payload)
        signature = sign_receipt_hash(receipt_hash)
        return ReceiptRecord(
            ride_id=ride_id,
            receipt_id=evidence.receipt_id,
            replay_id=f"replay-{ride_id}",
            status=evidence.replay.status,
            trace_hash=evidence.trace_hash,
            replay_hash=evidence.replay_hash,
            receipt_hash=receipt_hash,
            execution_fingerprint=execution_fingerprint(
                replay_hash=evidence.replay_hash,
                receipt_hash=receipt_hash,
                authority_hash=authority_hash,
            ),
            issued_at=evidence.generated_at,
            signature_validation=ReceiptSignature(
                signature_mode=SIGNATURE_MODE,
                signature=signature,
                all_signatures_valid=verify_receipt_signature(receipt_hash, signature),
            ),
        )


def _receipt_payload(evidence: EvidenceRecord) -> dict[str, Any]:
    authority_hash = evidence.canonical_dict()["authority"]["authority_hash"]
    return {
        "ride_id": evidence.ride_id,
        "trace_hash": evidence.trace_hash,
        "replay_hash": evidence.replay_hash,
        "authority_hash": authority_hash,
        "verification_status": evidence.verification_status,
        "reconstructed_status": evidence.replay.status,
        "reconstructed_assigned_driver": evidence.replay.assigned_driver,
        "reconstructed_passenger_id": evidence.replay.passenger_id,
        "transitions": list(evidence.replay.transitions),
    }


def _stable_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
