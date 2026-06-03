"""
afritech.distributed.recovery.recovery_protocol

Deterministic partition recovery from replay-verified ledger evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any


# ============================================================
# ERROR
# ============================================================

class RecoveryProtocolError(ValueError):
    pass


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_RECOVERY_STATUSES = {
    "RECOVERED",
    "RECOVERY_INVALID",
    "DUPLICATE_REJECTED",
    "MISSING_LEDGER_EVIDENCE",
}


# ============================================================
# HELPERS
# ============================================================

def _canonical_payload_hash(payload: Any) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise RecoveryProtocolError(f"{field} invalid")

    if "/" in value or "\\" in value or ".." in value:
        raise RecoveryProtocolError(f"{field} invalid")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise RecoveryProtocolError(f"{field} invalid")
    try:
        int(value, 16)
    except ValueError:
        raise RecoveryProtocolError(f"{field} invalid")


def _require_recovery_input(obj) -> None:
    if obj is None:
        raise RecoveryProtocolError("invalid input")

    for field in ("partition_id", "ledger_snapshot", "reason"):
        if not hasattr(obj, field):
            raise RecoveryProtocolError(f"invalid input: missing {field}")


def _sequence_reasons(entries) -> tuple[str, ...]:
    reasons = []
    seen = set()
    seqs = []

    for e in entries:
        if e.partition_sequence in seen:
            reasons.append("duplicate_sequence")
        seen.add(e.partition_sequence)
        seqs.append(e.partition_sequence)

    if seqs and sorted(seqs) != list(range(len(seqs))):
        reasons.append("sequence_gap")

    return tuple(sorted(set(reasons)))


# ============================================================
# INPUT
# ============================================================

@dataclass(frozen=True)
class RecoveryInput:
    partition_id: str
    ledger_snapshot: object
    reason: str

    def __post_init__(self) -> None:
        _require_identity(self.partition_id, "partition_id")

        if not hasattr(self.ledger_snapshot, "canonical_entries"):
            raise RecoveryProtocolError("invalid ledger_snapshot")

        if not callable(getattr(self.ledger_snapshot, "snapshot_hash", None)):
            raise RecoveryProtocolError("invalid ledger_snapshot")

        if not isinstance(self.reason, str) or not self.reason.strip():
            raise RecoveryProtocolError("invalid reason")

    def to_canonical_dict(self) -> dict[str, Any]:
        return {
            "partition_id": self.partition_id,
            "ledger_snapshot_hash": self.ledger_snapshot.snapshot_hash(),
            "reason": self.reason,
        }

    def input_hash(self) -> str:
        return _canonical_payload_hash(self.to_canonical_dict())


# ============================================================
# ENTRY
# ============================================================

@dataclass(frozen=True, order=True)
class RecoveredPartitionEntry:

    event_id: str
    partition_id: str
    partition_sequence: int
    input_hash: str
    output_hash: str
    execution_hash: str
    replay_hash: str
    source_ledger_entry_hash: str

    def __post_init__(self) -> None:
        _require_identity(self.event_id, "event_id")
        _require_identity(self.partition_id, "partition_id")

        if not isinstance(self.partition_sequence, int) or self.partition_sequence < 0:
            raise RecoveryProtocolError("invalid sequence")

        for field, value in (
            ("input_hash", self.input_hash),
            ("output_hash", self.output_hash),
            ("execution_hash", self.execution_hash),
            ("replay_hash", self.replay_hash),
            ("source_ledger_entry_hash", self.source_ledger_entry_hash),
        ):
            _require_sha256(value, field)

        if self.execution_hash != self.replay_hash:
            raise RecoveryProtocolError("execution/replay hash mismatch")

    @classmethod
    def from_ledger_entry(cls, entry):

        if entry is None:
            raise RecoveryProtocolError("invalid ledger entry")

        for field in (
            "event_id",
            "partition_id",
            "partition_sequence",
            "input_hash",
            "output_hash",
            "execution_hash",
            "replay_hash",
            "status",
        ):
            if not hasattr(entry, field):
                raise RecoveryProtocolError(f"invalid ledger entry: missing {field}")

        if entry.status != "REPLAY_VERIFIED":
            raise RecoveryProtocolError("non replay-verified entry")

        if not callable(getattr(entry, "entry_hash", None)):
            raise RecoveryProtocolError("invalid entry_hash")

        return cls(
            event_id=entry.event_id,
            partition_id=entry.partition_id,
            partition_sequence=entry.partition_sequence,
            input_hash=entry.input_hash,
            output_hash=entry.output_hash,
            execution_hash=entry.execution_hash,
            replay_hash=entry.replay_hash,
            source_ledger_entry_hash=entry.entry_hash(),
        )

    def to_canonical_dict(self):
        return {
            "event_id": self.event_id,
            "partition_id": self.partition_id,
            "partition_sequence": self.partition_sequence,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "execution_hash": self.execution_hash,
            "replay_hash": self.replay_hash,
            "source_ledger_entry_hash": self.source_ledger_entry_hash,
        }


# ============================================================
# STATE
# ============================================================

@dataclass(frozen=True)
class PartitionRecoveryState:

    partition_id: str
    recovered_entries: tuple[RecoveredPartitionEntry, ...]
    recovery_hash: str

    def __post_init__(self) -> None:
        _require_identity(self.partition_id, "partition_id")
        _require_sha256(self.recovery_hash, "recovery_hash")

        for entry in self.recovered_entries:
            if entry.partition_id != self.partition_id:
                raise RecoveryProtocolError("partition mismatch")

        expected = _canonical_payload_hash({
            "partition_id": self.partition_id,
            "recovered_entries": [
                e.to_canonical_dict() for e in self.canonical_entries()
            ],
        })

        if self.recovery_hash != expected:
            raise RecoveryProtocolError("recovery hash mismatch")

    def canonical_entries(self):
        return tuple(sorted(
            self.recovered_entries,
            key=lambda e: (
                e.partition_sequence,
                e.event_id,
                e.source_ledger_entry_hash,
            ),
        ))


# ============================================================
# REPORT
# ============================================================

@dataclass(frozen=True)
class RecoveryReport:
    recovered: bool
    status: str
    recovery_input_hash: str
    recovered_state_hash: str
    reasons: tuple[str, ...]
    report_hash_value: str


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class RecoveryResult:
    recovery_state: PartitionRecoveryState
    report: RecoveryReport


# ============================================================
# ENGINE (FINAL FIXED)
# ============================================================

class DistributedRecoveryProtocol:

    def recover_partition(self, recovery_input) -> RecoveryResult:

        _require_recovery_input(recovery_input)

        reasons = []

        # ✅ ONLY ACCEPT REPLAY_VERIFIED ENTRIES
        ledger_entries = tuple(
            e for e in recovery_input.ledger_snapshot.canonical_entries()
            if (
                hasattr(e, "partition_id")
                and e.partition_id == recovery_input.partition_id
                and getattr(e, "status", None) == "REPLAY_VERIFIED"
            )
        )

        # ✅ CRITICAL FIX
        if not ledger_entries:
            reasons.append("missing_ledger_evidence")

        entries = []

        for entry in ledger_entries:
            try:
                entries.append(RecoveredPartitionEntry.from_ledger_entry(entry))
            except RecoveryProtocolError:
                reasons.append("non_replay_verified_entry")

        # ✅ sequence validation
        seq_reasons = _sequence_reasons(entries)
        reasons.extend(seq_reasons)

        entries = sorted(
            entries,
            key=lambda e: (e.partition_sequence, e.event_id, e.source_ledger_entry_hash),
        )

        state_hash = _canonical_payload_hash({
            "partition_id": recovery_input.partition_id,
            "recovered_entries": [e.to_canonical_dict() for e in entries],
        })

        state = PartitionRecoveryState(
            partition_id=recovery_input.partition_id,
            recovered_entries=tuple(entries),
            recovery_hash=state_hash,
        )

        reasons = tuple(sorted(set(reasons)))

        # ✅ FINAL FIX
        success = (not reasons) and bool(entries)

        if success:
            status = "RECOVERED"
        elif "missing_ledger_evidence" in reasons:
            status = "MISSING_LEDGER_EVIDENCE"
        elif any("duplicate_sequence" in r for r in reasons):
            status = "DUPLICATE_REJECTED"
        else:
            status = "RECOVERY_INVALID"

        report_payload = {
            "recovered": success,
            "status": status,
            "recovery_input_hash": recovery_input.input_hash(),
            "recovered_state_hash": state.recovery_hash,
            "reasons": reasons,
        }

        report = RecoveryReport(
            recovered=success,
            status=status,
            recovery_input_hash=recovery_input.input_hash(),
            recovered_state_hash=state.recovery_hash,
            reasons=reasons,
            report_hash_value=_canonical_payload_hash(report_payload),
        )

        return RecoveryResult(state, report)


# ============================================================
# PUBLIC API
# ============================================================

def recover_partition_from_ledger(*, partition_id, ledger_snapshot, reason):
    return DistributedRecoveryProtocol().recover_partition(
        RecoveryInput(partition_id, ledger_snapshot, reason)
    )


def require_partition_recovered_from_ledger(**kwargs):
    result = recover_partition_from_ledger(**kwargs)

    if not result.report.recovered:
        raise RecoveryProtocolError(
            "recovery failed: " + ",".join(result.report.reasons)
        )

    return result


def build_recovery_input(*, partition_id, ledger_snapshot, reason):
    return RecoveryInput(partition_id, ledger_snapshot, reason)


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "RecoveryProtocolError",
    "RecoveryInput",
    "RecoveredPartitionEntry",
    "PartitionRecoveryState",
    "RecoveryReport",
    "RecoveryResult",
    "DistributedRecoveryProtocol",
    "recover_partition_from_ledger",
    "require_partition_recovered_from_ledger",
    "build_recovery_input",
]