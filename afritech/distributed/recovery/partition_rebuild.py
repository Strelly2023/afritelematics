"""
afritech.distributed.recovery.partition_rebuild

Deterministic partition rebuild from verified distributed ledger evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.distributed.recovery.recovery_protocol import (
    RecoveredPartitionEntry,
)


# ============================================================
# ERROR
# ============================================================

class PartitionRebuildError(ValueError):
    pass


# ============================================================
# CONSTANTS
# ============================================================

ALLOWED_REBUILD_STATUSES = {
    "REBUILT",
    "REBUILD_INVALID",
    "DUPLICATE_SEQUENCE",
    "SEQUENCE_GAP",
    "MISSING_LEDGER_EVIDENCE",
}


# ============================================================
# HELPERS
# ============================================================

def _canonical_payload_hash(payload: Any) -> str:
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _require_identity(value: str, field: str) -> None:
    if not isinstance(value, str) or not value:
        raise PartitionRebuildError(f"{field} invalid")

    if "/" in value or "\\" in value or ".." in value:
        raise PartitionRebuildError(f"{field} invalid")


def _require_sha256(value: str, field: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise PartitionRebuildError(f"{field} invalid")
    try:
        int(value, 16)
    except ValueError:
        raise PartitionRebuildError(f"{field} invalid")


def _require_input(obj) -> None:
    for field in ("partition_id", "ledger_snapshot", "reason"):
        if not hasattr(obj, field):
            raise PartitionRebuildError(f"invalid input: missing {field}")


def _require_entry(obj) -> None:
    for field in (
        "event_id",
        "partition_id",
        "partition_sequence",
        "execution_hash",
        "replay_hash",
    ):
        if not hasattr(obj, field):
            raise PartitionRebuildError("invalid entry")


# ============================================================
# INPUT
# ============================================================

@dataclass(frozen=True)
class PartitionRebuildInput:
    partition_id: str
    ledger_snapshot: object
    reason: str = "partition_rebuild"

    def __post_init__(self) -> None:
        _require_identity(self.partition_id, "partition_id")

        if not hasattr(self.ledger_snapshot, "canonical_entries"):
            raise PartitionRebuildError("invalid ledger_snapshot")

        if not callable(getattr(self.ledger_snapshot, "snapshot_hash", None)):
            raise PartitionRebuildError("invalid ledger_snapshot")

        if not isinstance(self.reason, str) or not self.reason:
            raise PartitionRebuildError("invalid reason")

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
class PartitionRebuildEntry:

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
            raise PartitionRebuildError("invalid sequence")

        for field, value in (
            ("input_hash", self.input_hash),
            ("output_hash", self.output_hash),
            ("execution_hash", self.execution_hash),
            ("replay_hash", self.replay_hash),
            ("source_ledger_entry_hash", self.source_ledger_entry_hash),
        ):
            _require_sha256(value, field)

        if self.execution_hash != self.replay_hash:
            raise PartitionRebuildError("execution/replay hash mismatch")

    @classmethod
    def from_ledger_entry(cls, entry):

        if entry is None:
            raise PartitionRebuildError("invalid ledger entry")

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
                raise PartitionRebuildError(f"invalid ledger entry: missing {field}")

        if entry.status != "REPLAY_VERIFIED":
            raise PartitionRebuildError("non replay-verified entry")

        if not callable(getattr(entry, "entry_hash", None)):
            raise PartitionRebuildError("invalid entry_hash")

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

    def to_canonical_dict(self) -> dict[str, Any]:
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

    def to_recovered_entry(self) -> RecoveredPartitionEntry:
        return RecoveredPartitionEntry(**self.to_canonical_dict())


# ============================================================
# STATE
# ============================================================

@dataclass(frozen=True)
class PartitionRebuildState:

    partition_id: str
    entries: tuple[PartitionRebuildEntry, ...]
    rebuild_hash: str

    def __post_init__(self) -> None:
        _require_identity(self.partition_id, "partition_id")
        _require_sha256(self.rebuild_hash, "rebuild_hash")

        for entry in self.entries:
            _require_entry(entry)

            if entry.partition_id != self.partition_id:
                raise PartitionRebuildError("partition mismatch")

        expected = _canonical_payload_hash({
            "partition_id": self.partition_id,
            "entries": [
                e.to_canonical_dict() for e in self.canonical_entries()
            ],
        })

        if self.rebuild_hash != expected:
            raise PartitionRebuildError("rebuild_hash mismatch")

    def canonical_entries(self):
        return tuple(sorted(
            self.entries,
            key=lambda e: (
                e.partition_sequence,
                e.event_id,
                e.source_ledger_entry_hash,
            ),
        ))

    def recovered_entries(self):
        return tuple(e.to_recovered_entry() for e in self.canonical_entries())


# ============================================================
# REPORT
# ============================================================

@dataclass(frozen=True)
class PartitionRebuildReport:

    rebuilt: bool
    status: str
    input_hash: str
    rebuild_hash: str
    reasons: tuple[str, ...]
    report_hash: str


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class PartitionRebuildResult:
    state: PartitionRebuildState
    report: PartitionRebuildReport


# ============================================================
# ENGINE
# ============================================================

class PartitionRebuilder:

    def rebuild(self, rebuild_input):

        _require_input(rebuild_input)

        reasons: list[str] = []

        ledger_entries = tuple(
            e for e in rebuild_input.ledger_snapshot.canonical_entries()
            if e.partition_id == rebuild_input.partition_id
        )

        if not ledger_entries:
            reasons.append("missing_ledger_evidence")

        entries: list[PartitionRebuildEntry] = []

        for e in ledger_entries:
            try:
                entries.append(PartitionRebuildEntry.from_ledger_entry(e))
            except PartitionRebuildError:
                reasons.append("non_replay_verified_entry")

        # ✅ sequence validation
        reasons.extend(_sequence_reasons(entries=tuple(entries)))

        # ✅ canonical ordering
        entries = sorted(
            entries,
            key=lambda e: (e.partition_sequence, e.event_id, e.source_ledger_entry_hash)
        )

        rebuild_hash = _canonical_payload_hash({
            "partition_id": rebuild_input.partition_id,
            "entries": [e.to_canonical_dict() for e in entries],
        })

        state = PartitionRebuildState(
            partition_id=rebuild_input.partition_id,
            entries=tuple(entries),
            rebuild_hash=rebuild_hash,
        )

        reasons = tuple(sorted(set(reasons)))
        rebuilt = not reasons
        status = _status_from_reasons(reasons)

        report_payload = {
            "rebuilt": rebuilt,
            "status": status,
            "input_hash": rebuild_input.input_hash(),
            "rebuild_hash": state.rebuild_hash,
            "reasons": reasons,
        }

        report = PartitionRebuildReport(
            rebuilt=rebuilt,
            status=status,
            input_hash=rebuild_input.input_hash(),
            rebuild_hash=state.rebuild_hash,
            reasons=reasons,
            report_hash=_canonical_payload_hash(report_payload),
        )

        return PartitionRebuildResult(state, report)


# ============================================================
# SEQUENCE VALIDATION
# ============================================================

def _sequence_reasons(*, entries):
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


def _status_from_reasons(reasons):
    if not reasons:
        return "REBUILT"
    if "missing_ledger_evidence" in reasons:
        return "MISSING_LEDGER_EVIDENCE"
    if "duplicate_sequence" in reasons:
        return "DUPLICATE_SEQUENCE"
    if "sequence_gap" in reasons:
        return "SEQUENCE_GAP"
    return "REBUILD_INVALID"


# ============================================================
# PUBLIC API
# ============================================================

def require_partition_rebuilt_from_ledger(
    *,
    partition_id: str,
    ledger_snapshot,
    reason: str,
):
    engine = PartitionRebuilder()

    result = engine.rebuild(
        PartitionRebuildInput(
            partition_id=partition_id,
            ledger_snapshot=ledger_snapshot,
            reason=reason,
        )
    )

    if not result.report.rebuilt:
        raise PartitionRebuildError(
            "partition rebuild failed: " + ",".join(result.report.reasons)
        )

    return result


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "PartitionRebuildError",
    "PartitionRebuildInput",
    "PartitionRebuildEntry",
    "PartitionRebuildState",
    "PartitionRebuildReport",
    "PartitionRebuildResult",
    "PartitionRebuilder",
    "require_partition_rebuilt_from_ledger",
]