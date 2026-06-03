"""
afritech.distributed.replay.distributed_execution_transcript
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Iterable, Mapping


# ============================================================
# ERROR
# ============================================================

class DistributedExecutionTranscriptError(ValueError):
    pass


# ============================================================
# ENTRY ✅ FIXED
# ============================================================

@dataclass(frozen=True, order=True)
class DistributedExecutionTranscriptEntry:

    batch_id: str
    event_id: str
    partition_id: str
    partition_sequence: int
    worker_id: str

    input_hash: str
    output_hash: str
    execution_hash: str
    replay_hash: str

    queue_record_hash: str
    worker_result_hash: str

    def __post_init__(self) -> None:
        _require_identity(self.batch_id, "batch_id")
        _require_identity(self.event_id, "event_id")
        _require_identity(self.partition_id, "partition_id")
        _require_identity(self.worker_id, "worker_id")

        if not isinstance(self.partition_sequence, int) or self.partition_sequence < 0:
            raise DistributedExecutionTranscriptError("invalid sequence")

        for name, value in (
            ("input_hash", self.input_hash),
            ("output_hash", self.output_hash),
            ("execution_hash", self.execution_hash),
            ("replay_hash", self.replay_hash),
            ("queue_record_hash", self.queue_record_hash),
            ("worker_result_hash", self.worker_result_hash),
        ):
            _require_sha256(value, name)

    # ---------------------------------------------------------
    # BUILDER ✅ CRITICAL FIX
    # ---------------------------------------------------------

    @classmethod
    def from_record_and_result(cls, *, batch_id: str, record, result):

        for field in ("event_id", "partition_id", "sequence"):
            if not hasattr(record, field):
                raise DistributedExecutionTranscriptError(
                    f"invalid record: missing {field}"
                )

        for field in (
            "event_id",
            "partition_id",
            "partition_sequence",
            "execution_hash",
            "replay_hash",
        ):
            if not hasattr(result, field):
                raise DistributedExecutionTranscriptError(
                    f"invalid result: missing {field}"
                )

        if record.event_id != result.event_id:
            raise DistributedExecutionTranscriptError("event mismatch")

        if record.partition_id != result.partition_id:
            raise DistributedExecutionTranscriptError("partition mismatch")

        if record.sequence != result.partition_sequence:
            raise DistributedExecutionTranscriptError("sequence mismatch")

        record_hash = (
            record.record_hash()
            if hasattr(record, "record_hash") and callable(record.record_hash)
            else _fallback_hash(record)
        )

        result_hash = (
            result.compute_canonical_hash()
            if hasattr(result, "compute_canonical_hash")
            else result.execution_hash
        )

        return cls(
            batch_id=batch_id,
            event_id=record.event_id,
            partition_id=record.partition_id,
            partition_sequence=record.sequence,
            worker_id=getattr(result, "worker_id", "unknown"),
            input_hash=getattr(result, "input_hash", record_hash),
            output_hash=getattr(result, "output_hash", result.execution_hash),
            execution_hash=result.execution_hash,
            replay_hash=result.replay_hash,
            queue_record_hash=record_hash,
            worker_result_hash=result_hash,
        )

    # ---------------------------------------------------------
    # CANONICAL
    # ---------------------------------------------------------

    def to_canonical_dict(self) -> dict[str, object]:
        return {
            "batch_id": self.batch_id,
            "event_id": self.event_id,
            "execution_hash": self.execution_hash,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "partition_id": self.partition_id,
            "partition_sequence": self.partition_sequence,
            "queue_record_hash": self.queue_record_hash,
            "replay_hash": self.replay_hash,
            "worker_id": self.worker_id,
            "worker_result_hash": self.worker_result_hash,
        }

    def canonical_json(self) -> str:
        return json.dumps(
            self.to_canonical_dict(),
            sort_keys=True,
            separators=(",", ":"),
        )

    def entry_hash(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# TRANSCRIPT ✅ FIXED
# ============================================================

@dataclass(frozen=True)
class DistributedExecutionTranscript:

    transcript_id: str
    entries: tuple[DistributedExecutionTranscriptEntry, ...]

    def __post_init__(self) -> None:
        _require_identity(self.transcript_id, "transcript_id")

        if not isinstance(self.entries, tuple) or not self.entries:
            raise DistributedExecutionTranscriptError("invalid entries")

        seen = set()

        for entry in self.entries:
            if entry is None:
                raise DistributedExecutionTranscriptError("invalid entry")

            identity = (
                entry.batch_id,
                entry.partition_id,
                entry.partition_sequence,
                entry.event_id,
            )

            if identity in seen:
                raise DistributedExecutionTranscriptError("duplicate entry")

            seen.add(identity)

        expected = self._derive_transcript_id(self.canonical_entries())

        if self.transcript_id != expected:
            raise DistributedExecutionTranscriptError("transcript_id mismatch")

    # ---------------------------------------------------------
    # BUILD
    # ---------------------------------------------------------

    @classmethod
    def create(cls, entries: Iterable[DistributedExecutionTranscriptEntry]):

        canonical = _canonical_entries(tuple(entries))

        if not canonical:
            raise DistributedExecutionTranscriptError("empty transcript")

        return cls(
            transcript_id=cls._derive_transcript_id(canonical),
            entries=canonical,
        )

    @staticmethod
    def _derive_transcript_id(entries):
        payload = {
            "entries": [e.to_canonical_dict() for e in _canonical_entries(entries)]
        }
        return "distributed_transcript." + _canonical_payload_hash(payload)

    # ---------------------------------------------------------
    # ACCESSORS
    # ---------------------------------------------------------

    def canonical_entries(self):
        return _canonical_entries(self.entries)

    def canonical_json(self) -> str:
        return json.dumps(
            {
                "entries": [e.to_canonical_dict() for e in self.canonical_entries()],
                "transcript_id": self.transcript_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        )

    def transcript_hash(self) -> str:
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# CI VALIDATION ENTRYPOINT ✅
# ============================================================

def require_valid_distributed_execution_transcript(transcript):

    if transcript is None:
        raise DistributedExecutionTranscriptError("invalid transcript")

    if not hasattr(transcript, "entries") or not hasattr(transcript, "transcript_id"):
        raise DistributedExecutionTranscriptError("invalid transcript structure")

    if not isinstance(transcript.entries, tuple) or not transcript.entries:
        raise DistributedExecutionTranscriptError("invalid entries")

    for entry in transcript.entries:
        if entry is None:
            raise DistributedExecutionTranscriptError("invalid entry")

        for field in (
            "event_id",
            "partition_id",
            "partition_sequence",
            "execution_hash",
        ):
            if not hasattr(entry, field):
                raise DistributedExecutionTranscriptError(
                    f"invalid entry: missing {field}"
                )

    return transcript


# ============================================================
# VERIFICATION ✅
# ============================================================

@dataclass(frozen=True)
class DistributedExecutionTranscriptVerification:
    valid: bool
    status: str
    transcript_hash: str
    reasons: tuple[str, ...]


def verify_distributed_execution_transcript(transcript):

    if transcript is None or not hasattr(transcript, "entries"):
        raise DistributedExecutionTranscriptError("invalid transcript")

    reasons = []
    seen = set()
    seq_map = {}

    for entry in transcript.canonical_entries():

        identity = (
            entry.batch_id,
            entry.partition_id,
            entry.partition_sequence,
            entry.event_id,
        )

        if identity in seen:
            reasons.append("duplicate_entry")

        seen.add(identity)

        seq_map.setdefault(entry.partition_id, []).append(entry.partition_sequence)

        if len(entry.entry_hash()) != 64:
            reasons.append("invalid_entry_hash")

        if entry.execution_hash != entry.replay_hash:
            reasons.append("execution_replay_mismatch")

    for pid, seqs in seq_map.items():
        if sorted(seqs) != list(range(len(seqs))):
            reasons.append(f"sequence_gap:{pid}")

    expected = DistributedExecutionTranscript._derive_transcript_id(
        transcript.canonical_entries()
    )

    if transcript.transcript_id != expected:
        reasons.append("transcript_id_mismatch")

    return DistributedExecutionTranscriptVerification(
        valid=not reasons,
        status="VALID" if not reasons else "INVALID",
        transcript_hash=transcript.transcript_hash(),
        reasons=tuple(sorted(set(reasons))),
    )


# ============================================================
# HELPERS
# ============================================================

def _canonical_entries(entries):
    return tuple(
        sorted(
            entries,
            key=lambda e: (
                e.batch_id,
                e.partition_id,
                e.partition_sequence,
                e.event_id,
                e.worker_id,
                e.entry_hash(),
            ),
        )
    )


def _canonical_payload_hash(payload: Mapping[str, object]) -> str:
    return sha256(
        json.dumps(dict(payload), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _fallback_hash(obj) -> str:
    return sha256(
        json.dumps(
            str(obj),
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def _require_identity(value: str, field: str):
    if not isinstance(value, str) or not value:
        raise DistributedExecutionTranscriptError(f"{field} invalid")


def _require_sha256(value: str, field: str):
    if not isinstance(value, str) or len(value) != 64:
        raise DistributedExecutionTranscriptError(f"{field} invalid sha256")

    try:
        int(value, 16)
    except ValueError:
        raise DistributedExecutionTranscriptError(f"{field} invalid hex")


# ============================================================
# CI HELPER ✅
# ============================================================

def transcript_from_mappings(
    *,
    transcript_id: str | None,
    entries: Iterable[Mapping[str, object]],
):

    if entries is None:
        raise DistributedExecutionTranscriptError("entries required")

    built_entries = []

    for raw in entries:

        if raw is None or not isinstance(raw, Mapping):
            raise DistributedExecutionTranscriptError("invalid entry mapping")

        required_fields = (
            "batch_id",
            "event_id",
            "partition_id",
            "partition_sequence",
            "worker_id",
            "input_hash",
            "output_hash",
            "execution_hash",
            "replay_hash",
            "queue_record_hash",
            "worker_result_hash",
        )

        for field in required_fields:
            if field not in raw:
                raise DistributedExecutionTranscriptError(f"missing field: {field}")

        built_entries.append(
            DistributedExecutionTranscriptEntry(
                batch_id=raw["batch_id"],
                event_id=raw["event_id"],
                partition_id=raw["partition_id"],
                partition_sequence=raw["partition_sequence"],
                worker_id=raw["worker_id"],
                input_hash=raw["input_hash"],
                output_hash=raw["output_hash"],
                execution_hash=raw["execution_hash"],
                replay_hash=raw["replay_hash"],
                queue_record_hash=raw["queue_record_hash"],
                worker_result_hash=raw["worker_result_hash"],
            )
        )

    transcript = DistributedExecutionTranscript.create(built_entries)

    if transcript_id is not None and transcript.transcript_id != transcript_id:
        raise DistributedExecutionTranscriptError("provided transcript_id mismatch")

    return transcript