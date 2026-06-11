"""Evidence derivation from persisted trace and deterministic replay."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from afriride_system.backend.authority_runtime import DOC_VERSION, authority_envelope
from afriride_system.backend.replay_engine import ReplayEngine, ReplaySnapshot
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
class EvidenceRecord:
    ride_id: str
    trace_hash: str
    replay_hash: str
    verification_status: str
    receipt_id: str
    generated_at: str
    replay: ReplaySnapshot

    def canonical_dict(self) -> dict[str, Any]:
        return {
            "ride_id": self.ride_id,
            "trace_hash": self.trace_hash,
            "replay_hash": self.replay_hash,
            "verification_status": self.verification_status,
            "receipt_id": self.receipt_id,
            "generated_at": self.generated_at,
            "replay_verified": self.replay.replay_verified,
            "reconstructed_status": self.replay.status,
            "reconstructed_assigned_driver": self.replay.assigned_driver,
            "authority": authority_envelope(
                doc_id=__doc_authority__,
                doc_version=__doc_version__,
                governed_invariants=__governed_invariants__,
                surface="evidence_record",
            ),
        }


class EvidenceEngine:
    def __init__(self, replay_engine: ReplayEngine | None = None) -> None:
        self.replay_engine = replay_engine or ReplayEngine()

    def derive(self, ride_id: str, events: tuple[TraceEvent, ...]) -> EvidenceRecord:
        replay = self.replay_engine.replay(ride_id, events)
        verification_status = "VERIFIED" if replay.replay_verified else "REJECTED"
        return EvidenceRecord(
            ride_id=ride_id,
            trace_hash=replay.trace_hash,
            replay_hash=replay.replay_hash,
            verification_status=verification_status,
            receipt_id=f"receipt-{ride_id}",
            generated_at=_now_iso(),
            replay=replay,
        )


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
