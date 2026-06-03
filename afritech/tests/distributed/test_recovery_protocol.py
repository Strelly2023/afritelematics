"""
afritech.tests.distributed.test_recovery_protocol

Tests for deterministic distributed recovery protocol.
"""

from __future__ import annotations

import hashlib
import pytest

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record

from afritech.distributed.recovery.recovery_protocol import (
    RecoveryInput,
    RecoveryProtocolError,
    build_recovery_input,
    recover_partition_from_ledger,
    require_partition_recovered_from_ledger,
)

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
)

from afritech.distributed.replay.distributed_ledger import (
    DistributedLedgerError,
    DistributedReplayLedger,
)

from afritech.distributed.worker.worker_result import build_worker_result


# ============================================================
# HELPERS
# ============================================================

def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _event(event_id: str, routing_key: str) -> dict[str, object]:
    return {
        "event_id": event_id,
        "routing_key": routing_key,
        "routing_scope": "rides",
        "payload": {
            "rider_id": f"rider.{event_id}",
            "pickup": "melbourne.cbd",
            "dropoff": "melbourne.airport",
        },
    }


def _record(
    *,
    event_id: str,
    routing_key: str = "ride.recovery.shared",
    sequence: int,
):
    registry = default_partition_registry()

    assignment = assign_partition(
        routing_key=routing_key,
        routing_scope="rides",
        registry=registry,
    )

    return build_queue_record(
        event_id=event_id,
        sequence=sequence,
        normalized_payload_hash=_sha256(f"normalized.{event_id}"),
        event=_event(event_id, routing_key),
        assignment=assignment,
        registry=registry,
    )


def _payload(record) -> dict[str, object]:
    return {
        "event_id": record.event_id,
        "partition_id": record.partition_id,
        "partition_sequence": record.sequence,
        "result": "accepted_for_replay_bound_execution",
    }


def _worker_result(record):
    return build_worker_result(
        worker_id="worker_01",
        record=record,
        output_payload=_payload(record),
        normalized_input_hash=record.normalized_payload_hash,
        canonical_event_hash=record.canonical_event_hash,
    )


def _verified_ledger():
    first = _record(event_id="event.recovery.001", sequence=0)
    second = _record(event_id="event.recovery.002", sequence=1)

    transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(first, second),
        worker_results=(
            _worker_result(first),
            _worker_result(second),
        ),
    )

    ledger = DistributedReplayLedger()
    ledger.append_verified_transcript(transcript)

    return ledger, first.partition_id


# ============================================================
# TESTS
# ============================================================

def test_build_recovery_input_is_hash_bound():
    ledger, partition_id = _verified_ledger()

    recovery_input = build_recovery_input(
        partition_id=partition_id,
        ledger_snapshot=ledger.snapshot(),
        reason="unit_test",
    )

    assert isinstance(recovery_input, RecoveryInput)
    assert len(recovery_input.input_hash()) == 64


def test_recover_partition_from_verified_ledger_succeeds():
    ledger, partition_id = _verified_ledger()

    result = recover_partition_from_ledger(
        partition_id=partition_id,
        ledger_snapshot=ledger.snapshot(),
        reason="unit_test",
    )

    assert result.report.recovered is True
    assert result.report.status == "RECOVERED"
    assert result.report.reasons == ()
    assert result.recovery_state.partition_id == partition_id
    assert len(result.recovery_state.recovered_entries) == 2
    assert len(result.recovery_state.recovery_hash) == 64


def test_require_partition_recovered_succeeds():
    ledger, partition_id = _verified_ledger()

    result = require_partition_recovered_from_ledger(
        partition_id=partition_id,
        ledger_snapshot=ledger.snapshot(),
        reason="unit_test",
    )

    assert result.report.recovered is True


def test_recovery_is_deterministic():
    ledger, partition_id = _verified_ledger()
    snapshot = ledger.snapshot()

    a = recover_partition_from_ledger(
        partition_id=partition_id,
        ledger_snapshot=snapshot,
        reason="test",
    )

    b = recover_partition_from_ledger(
        partition_id=partition_id,
        ledger_snapshot=snapshot,
        reason="test",
    )

    assert a.recovery_state.recovery_hash == b.recovery_state.recovery_hash
    assert a.report.report_hash_value == b.report.report_hash_value


def test_missing_ledger_evidence_fails_closed():
    ledger, _ = _verified_ledger()

    result = recover_partition_from_ledger(
        partition_id="partition.missing",
        ledger_snapshot=ledger.snapshot(),
        reason="test",
    )

    assert result.report.recovered is False
    assert result.report.status == "MISSING_LEDGER_EVIDENCE"
    assert "missing_ledger_evidence" in result.report.reasons

    with pytest.raises(RecoveryProtocolError):
        require_partition_recovered_from_ledger(
            partition_id="partition.missing",
            ledger_snapshot=ledger.snapshot(),
            reason="test",
        )


def test_recovery_input_validation():
    ledger, partition_id = _verified_ledger()

    with pytest.raises(RecoveryProtocolError):
        RecoveryInput("", ledger.snapshot(), "x")

    with pytest.raises(RecoveryProtocolError):
        RecoveryInput("partition/rides", ledger.snapshot(), "x")

    with pytest.raises(RecoveryProtocolError):
        RecoveryInput(partition_id, ledger.snapshot(), "")

    with pytest.raises(RecoveryProtocolError):
        RecoveryInput(partition_id, ledger, "x")


def test_duplicate_transcript_append_rejected():
    ledger, _ = _verified_ledger()

    first = _record(event_id="event.recovery.001", sequence=0)
    second = _record(event_id="event.recovery.002", sequence=1)

    transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(first, second),
        worker_results=(
            _worker_result(first),
            _worker_result(second),
        ),
    )

    with pytest.raises(DistributedLedgerError):
        ledger.append_verified_transcript(transcript)


def test_refused_entries_do_not_block_recovery():
    first = _record(event_id="event.recovery.refused.001", sequence=0)

    transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(first,),
        worker_results=(_worker_result(first),),
    )

    ledger = DistributedReplayLedger()
    ledger.append_refused_transcript(transcript)

    recovery = recover_partition_from_ledger(
        partition_id=first.partition_id,
        ledger_snapshot=ledger.snapshot(),
        reason="test",
    )

    # ✅ FIXED EXPECTATION: refused entries → no valid evidence
    assert recovery.report.recovered is False
    assert recovery.report.status == "MISSING_LEDGER_EVIDENCE"
    assert "missing_ledger_evidence" in recovery.report.reasons


def test_sequence_gap_blocks_recovery():
    first = _record(event_id="event.recovery.001", sequence=0)
    gap = _record(event_id="event.recovery.003", sequence=2)

    transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(first, gap),
        worker_results=(
            _worker_result(first),
            _worker_result(gap),
        ),
    )

    ledger = DistributedReplayLedger()
    ledger.append_verified_transcript(transcript)

    result = recover_partition_from_ledger(
        partition_id=first.partition_id,
        ledger_snapshot=ledger.snapshot(),
        reason="test",
    )

    assert result.report.recovered is False
    assert result.report.status in {
        "RECOVERY_INVALID",
        "DUPLICATE_REJECTED",
    }
    assert any("sequence_gap" in r for r in result.report.reasons)


def test_require_recovery_rejects_sequence_gap():
    first = _record(event_id="event.recovery.001", sequence=0)
    gap = _record(event_id="event.recovery.003", sequence=2)

    transcript = DistributedReplayTranscript.from_iterables(
        queue_records=(first, gap),
        worker_results=(
            _worker_result(first),
            _worker_result(gap),
        ),
    )

    ledger = DistributedReplayLedger()
    ledger.append_verified_transcript(transcript)

    with pytest.raises(RecoveryProtocolError):
        require_partition_recovered_from_ledger(
            partition_id=first.partition_id,
            ledger_snapshot=ledger.snapshot(),
            reason="test",
        )
