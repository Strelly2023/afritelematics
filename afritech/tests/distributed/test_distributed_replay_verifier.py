"""
afritech.tests.distributed.test_distributed_replay_verifier

Tests for distributed replay verification.
"""

from __future__ import annotations

import hashlib
import pytest

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record

from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    DistributedReplayVerificationError,
    DistributedWorkerResult,
    build_worker_result,
    require_distributed_replay_verified,
    verify_distributed_replay,
)


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


def _build_record(*, event_id: str, routing_key: str, sequence: int):
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


def _payload(record):
    return {
        "event_id": record.event_id,
        "partition_id": record.partition_id,
        "partition_sequence": record.sequence,
        "result": "accepted_for_replay_bound_execution",
    }


def _build_worker(record):
    return build_worker_result(
        worker_id="worker_01",
        record=record,
        output_payload=_payload(record),
        normalized_input_hash=record.normalized_payload_hash,
        canonical_event_hash=record.canonical_event_hash,
    )


def _valid_records_and_results():
    first = _build_record(
        event_id="event.replay.001",
        routing_key="ride.replay.001",
        sequence=0,
    )

    second = _build_record(
        event_id="event.replay.002",
        routing_key="ride.replay.001",  # same partition
        sequence=1,
    )

    r1 = _build_worker(first)
    r2 = _build_worker(second)

    return (first, second), (r1, r2)


# ============================================================
# TESTS
# ============================================================

def test_valid_distributed_replay_transcript_verifies():
    records, results = _valid_records_and_results()

    report = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(records, results)
    )

    assert report.verified is True
    assert report.status == "VERIFIED"
    assert report.failure_modes == []
    assert report.distributed_execution_hash == report.replay_reconstruction_hash


def test_require_distributed_replay_verified_returns_report():
    records, results = _valid_records_and_results()

    report = require_distributed_replay_verified(
        DistributedReplayTranscript.from_iterables(records, results)
    )

    assert report.verified is True


def test_missing_worker_result_fails_verification():
    records, results = _valid_records_and_results()

    transcript = DistributedReplayTranscript.from_iterables(records, (results[0],))
    report = verify_distributed_replay(transcript)

    assert report.verified is False

    with pytest.raises(DistributedReplayVerificationError):
        require_distributed_replay_verified(transcript)


def test_duplicate_worker_result_fails_verification():
    records, results = _valid_records_and_results()

    report = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(
            (records[0],),
            (results[0], results[0]),
        )
    )

    assert report.verified is False


def test_duplicate_queue_record_fails_verification():
    records, results = _valid_records_and_results()

    report = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(
            (records[0], records[0]),
            (results[0],),
        )
    )

    assert report.verified is False


def test_worker_replay_hash_tampering_detected():
    records, results = _valid_records_and_results()
    original = results[0]

    # ✅ Correct WorkerResult construction (NO forbidden args)
    tampered = DistributedWorkerResult.from_output(
        worker_id=original.worker_id,
        record=records[0],
        output=dict(original.output),
        normalized_input_hash=original.normalized_input_hash,
        canonical_event_hash=original.canonical_event_hash,
    )

    # manually override hashes
    object.__setattr__(tampered, "event_id", original.event_id)
    object.__setattr__(tampered, "partition_id", original.partition_id)
    object.__setattr__(tampered, "partition_sequence", original.partition_sequence)

    object.__setattr__(tampered, "replay_hash", _sha256("tampered"))

    report = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables((records[0],), (tampered,))
    )

    assert report.verified is False


def test_divergent_worker_output_fails_verification():
    records, results = _valid_records_and_results()

    bad = build_worker_result(
        worker_id="worker_01",
        record=records[1],
        output_payload={**_payload(records[1]), "result": "BAD"},
        normalized_input_hash=records[1].normalized_payload_hash,
        canonical_event_hash=records[1].canonical_event_hash,
    )

    report = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables(records, (results[0], bad))
    )

    assert report.verified is False


def test_partition_sequence_gap_not_detected_by_verifier():
    first = _build_record(
        event_id="event.replay.001",
        routing_key="ride.replay.001",
        sequence=0,
    )

    gap = _build_record(
        event_id="event.replay.003",
        routing_key="ride.replay.001",
        sequence=2,
    )

    r1 = _build_worker(first)
    r2 = _build_worker(gap)

    report = verify_distributed_replay(
        DistributedReplayTranscript.from_iterables((first, gap), (r1, r2))
    )

    # by design, verifier does NOT enforce sequence continuity
    assert report.verified is True


def test_report_hash_is_deterministic():
    records, results = _valid_records_and_results()

    transcript = DistributedReplayTranscript.from_iterables(records, results)

    a = verify_distributed_replay(transcript)
    b = verify_distributed_replay(transcript)

    assert a.report_hash() == b.report_hash()