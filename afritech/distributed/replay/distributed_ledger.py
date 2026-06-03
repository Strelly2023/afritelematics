"""
afritech.distributed.replay.distributed_ledger
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    DistributedReplayVerificationReport,
    verify_distributed_replay,
)


# ============================================================
# ERROR
# ============================================================

class DistributedLedgerError(ValueError):
    pass


# ============================================================
# ENTRY
# ============================================================

@dataclass(frozen=True, order=True)
class DistributedLedgerEntry:

    event_id: str
    partition_id: str
    worker_id: str
    partition_sequence: int

    input_hash: str
    output_hash: str
    execution_hash: str
    replay_hash: str

    transcript_hash: str
    verification_report_hash: str

    status: str

    def __post_init__(self):
        _require_identity(self.event_id, "event_id")
        _require_identity(self.partition_id, "partition_id")
        _require_identity(self.worker_id, "worker_id")

        if not isinstance(self.partition_sequence, int) or self.partition_sequence < 0:
            raise DistributedLedgerError("invalid sequence")

        for field, value in (
            ("input_hash", self.input_hash),
            ("output_hash", self.output_hash),
            ("execution_hash", self.execution_hash),
            ("replay_hash", self.replay_hash),
            ("transcript_hash", self.transcript_hash),
            ("verification_report_hash", self.verification_report_hash),
        ):
            _require_sha256(value, field)

        if self.status not in {"REPLAY_VERIFIED", "REFUSED"}:
            raise DistributedLedgerError("invalid status")

    def to_canonical_dict(self):
        return {
            "event_id": self.event_id,
            "partition_id": self.partition_id,
            "partition_sequence": self.partition_sequence,
            "worker_id": self.worker_id,
            "input_hash": self.input_hash,
            "output_hash": self.output_hash,
            "execution_hash": self.execution_hash,
            "replay_hash": self.replay_hash,
            "transcript_hash": self.transcript_hash,
            "verification_report_hash": self.verification_report_hash,
            "status": self.status,
        }

    def canonical_json(self):
        return json.dumps(self.to_canonical_dict(), sort_keys=True, separators=(",", ":"))

    def entry_hash(self):
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# SNAPSHOT ✅ FIXED
# ============================================================

@dataclass(frozen=True)
class DistributedLedgerSnapshot:

    entries: tuple[DistributedLedgerEntry, ...]

    def __post_init__(self):
        if not isinstance(self.entries, tuple):
            raise DistributedLedgerError("entries must be tuple")

    # ✅ ONLY RETURN VERIFIED ENTRIES
    def canonical_entries(self):
        return tuple(
            sorted(
                (
                    e for e in self.entries
                    if e.status == "REPLAY_VERIFIED"
                ),
                key=lambda e: (
                    e.partition_id,
                    e.partition_sequence,
                    e.event_id,
                    e.worker_id,
                    e.entry_hash(),
                ),
            )
        )

    def canonical_json(self):
        return json.dumps(
            [e.to_canonical_dict() for e in self.canonical_entries()],
            sort_keys=True,
            separators=(",", ":"),
        )

    def snapshot_hash(self):
        return sha256(self.canonical_json().encode()).hexdigest()


# ============================================================
# RESULT
# ============================================================

@dataclass(frozen=True)
class DistributedLedgerAppendResult:
    appended_entries: tuple[DistributedLedgerEntry, ...]
    verification_report: DistributedReplayVerificationReport
    ledger_snapshot_hash: str


# ============================================================
# LEDGER ✅ FIXED
# ============================================================

class DistributedReplayLedger:

    def __init__(self):
        self._entries: list[DistributedLedgerEntry] = []

    def append_verified_transcript(self, transcript: DistributedReplayTranscript):

        report = verify_distributed_replay(transcript)

        if not report.verified:
            raise DistributedLedgerError(
                "cannot append unverified transcript: "
                + ", ".join(report.failure_modes or [])
            )

        entries = _entries_from_transcript(
            transcript=transcript,
            report=report,
            status="REPLAY_VERIFIED",
        )

        self._append(entries)

        return DistributedLedgerAppendResult(
            appended_entries=entries,
            verification_report=report,
            ledger_snapshot_hash=self.snapshot().snapshot_hash(),
        )

    # ✅ CRITICAL FIX
    def append_refused_transcript(self, transcript: DistributedReplayTranscript):

        report = verify_distributed_replay(transcript)

        # 🚫 DO NOT STORE REFUSED ENTRIES
        return DistributedLedgerAppendResult(
            appended_entries=tuple(),
            verification_report=report,
            ledger_snapshot_hash=self.snapshot().snapshot_hash(),
        )

    def snapshot(self):
        return DistributedLedgerSnapshot(entries=tuple(self._entries))

    def _append(self, new_entries):

        if not new_entries:
            raise DistributedLedgerError("empty append")

        seen = {
            (e.partition_id, e.partition_sequence, e.event_id)
            for e in self._entries
        }

        for entry in new_entries:
            key = (entry.partition_id, entry.partition_sequence, entry.event_id)

            if key in seen:
                raise DistributedLedgerError("duplicate append")

            seen.add(key)

        self._entries.extend(new_entries)


# ============================================================
# BUILDERS
# ============================================================

def _entries_from_transcript(*, transcript, report, status):

    records = transcript.records
    results = transcript.results

    if len(records) != len(results):
        raise DistributedLedgerError("record/result mismatch")

    entries = []

    for record, result in zip(records, results):

        record_hash = (
            record.record_hash()
            if hasattr(record, "record_hash")
            else _fallback_hash(record)
        )

        output_hash = getattr(result, "output_hash", result.execution_hash)

        entries.append(
            DistributedLedgerEntry(
                event_id=record.event_id,
                partition_id=record.partition_id,
                worker_id=result.worker_id,
                partition_sequence=record.sequence,
                input_hash=record_hash,
                output_hash=output_hash,
                execution_hash=result.execution_hash,
                replay_hash=result.replay_hash,
                transcript_hash=report.transcript_hash,
                verification_report_hash=report.report_hash(),
                status=status,
            )
        )

    return tuple(entries)


# ============================================================
# HELPERS
# ============================================================

def _fallback_hash(obj):
    return sha256(
        json.dumps(str(obj), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _require_identity(value: str, field: str):
    if not isinstance(value, str) or not value:
        raise DistributedLedgerError(f"{field} invalid")


def _require_sha256(value: str, field: str):
    if not isinstance(value, str) or len(value) != 64:
        raise DistributedLedgerError(f"{field} invalid")
    try:
        int(value, 16)
    except ValueError:
        raise DistributedLedgerError(f"{field} invalid")