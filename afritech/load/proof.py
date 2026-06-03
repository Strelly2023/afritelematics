"""Deterministic load proof harness for replay-governed execution."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record
from afritech.distributed.replay.distributed_replay_verifier import (
    DistributedReplayTranscript,
    require_distributed_replay_verified,
)
from afritech.distributed.worker.worker_result import build_worker_result


DEFAULT_LOAD_PROFILES = (1_000, 10_000, 100_000)


class LoadProofError(RuntimeError):
    """Raised when load replay proof detects divergence."""


@dataclass(frozen=True)
class LoadProofRun:
    event_count: int
    replay_hash: str
    partition_order_hash: str
    worker_result_hash: str
    event_source_hash: str
    record_hash: str
    report_hash: str
    verified: bool
    hidden_mutation_detected: bool

    def canonical_dict(self) -> dict[str, object]:
        return {
            "event_count": self.event_count,
            "event_source_hash": self.event_source_hash,
            "hidden_mutation_detected": self.hidden_mutation_detected,
            "partition_order_hash": self.partition_order_hash,
            "record_hash": self.record_hash,
            "replay_hash": self.replay_hash,
            "report_hash": self.report_hash,
            "verified": self.verified,
            "worker_result_hash": self.worker_result_hash,
        }


@dataclass(frozen=True)
class LoadProofProfile:
    event_count: int
    first_run: LoadProofRun
    replay_run: LoadProofRun

    @property
    def replay_hash_stable(self) -> bool:
        return self.first_run.replay_hash == self.replay_run.replay_hash

    @property
    def partition_order_stable(self) -> bool:
        return (
            self.first_run.partition_order_hash
            == self.replay_run.partition_order_hash
        )

    @property
    def worker_result_stable(self) -> bool:
        return self.first_run.worker_result_hash == self.replay_run.worker_result_hash

    @property
    def hidden_mutation_absent(self) -> bool:
        return (
            not self.first_run.hidden_mutation_detected
            and not self.replay_run.hidden_mutation_detected
            and self.first_run.event_source_hash == self.replay_run.event_source_hash
            and self.first_run.record_hash == self.replay_run.record_hash
        )

    @property
    def verified(self) -> bool:
        return (
            self.first_run.verified
            and self.replay_run.verified
            and self.replay_hash_stable
            and self.partition_order_stable
            and self.worker_result_stable
            and self.hidden_mutation_absent
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "event_count": self.event_count,
            "first_run": self.first_run.canonical_dict(),
            "hidden_mutation_absent": self.hidden_mutation_absent,
            "partition_order_stable": self.partition_order_stable,
            "replay_hash_stable": self.replay_hash_stable,
            "replay_run": self.replay_run.canonical_dict(),
            "verified": self.verified,
            "worker_result_stable": self.worker_result_stable,
        }


@dataclass(frozen=True)
class LoadProofReport:
    profiles: tuple[LoadProofProfile, ...]

    @property
    def verified(self) -> bool:
        return bool(self.profiles) and all(profile.verified for profile in self.profiles)

    def canonical_dict(self) -> dict[str, object]:
        return {
            "profiles": [profile.canonical_dict() for profile in self.profiles],
            "required_proofs": [
                "same_replay_hash",
                "same_partition_order",
                "same_worker_result",
                "no_hidden_mutation",
            ],
            "schema": "afritech.load_proof_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def run_required_load_proofs(
    event_counts: Iterable[int] = DEFAULT_LOAD_PROFILES,
) -> LoadProofReport:
    profiles = tuple(run_load_profile(count) for count in event_counts)
    report = LoadProofReport(profiles=profiles)
    if not report.verified:
        raise LoadProofError("load proof report failed verification")
    return report


def run_load_profile(event_count: int) -> LoadProofProfile:
    _require_event_count(event_count)
    source_events = tuple(_event(i) for i in range(event_count))
    first_run = _execute_load(source_events)
    replay_run = _execute_load(tuple(dict(event) for event in source_events))
    profile = LoadProofProfile(
        event_count=event_count,
        first_run=first_run,
        replay_run=replay_run,
    )
    if not profile.verified:
        raise LoadProofError(f"load profile failed verification: {event_count}")
    return profile


def _execute_load(events: tuple[Mapping[str, object], ...]) -> LoadProofRun:
    registry = default_partition_registry()
    source_hash_before = _canonical_hash(list(events))
    partition_sequences: dict[str, int] = {}
    records = []
    results = []

    for event in events:
        event_id = _require_string(event.get("event_id"), "event_id")
        routing_key = _require_string(event.get("routing_key"), "routing_key")
        routing_scope = _require_string(event.get("routing_scope"), "routing_scope")
        assignment = assign_partition(
            routing_key=routing_key,
            routing_scope=routing_scope,
            registry=registry,
        )
        sequence = partition_sequences.get(assignment.partition_id, 0)
        partition_sequences[assignment.partition_id] = sequence + 1
        normalized_payload_hash = _canonical_hash(
            {
                "event_id": event_id,
                "normalized_payload": event.get("payload", {}),
                "routing_key": routing_key,
                "routing_scope": routing_scope,
            }
        )
        record = build_queue_record(
            event_id=event_id,
            sequence=sequence,
            normalized_payload_hash=normalized_payload_hash,
            event=event,
            assignment=assignment,
            registry=registry,
        )
        output = {
            "event_id": record.event_id,
            "partition_id": record.partition_id,
            "partition_sequence": record.sequence,
            "result": "accepted_for_replay_bound_execution",
        }
        result = build_worker_result(
            worker_id=f"worker.{record.partition_id}",
            record=record,
            output_payload=output,
            normalized_input_hash=record.normalized_payload_hash,
            canonical_event_hash=record.canonical_event_hash,
        )
        records.append(record)
        results.append(result)

    source_hash_after = _canonical_hash(list(events))
    report = require_distributed_replay_verified(
        DistributedReplayTranscript.from_iterables(records, results)
    )

    return LoadProofRun(
        event_count=len(events),
        event_source_hash=source_hash_after,
        hidden_mutation_detected=source_hash_before != source_hash_after,
        partition_order_hash=_partition_order_hash(records),
        record_hash=_canonical_hash([record.to_canonical_dict() for record in records]),
        replay_hash=report.replay_reconstruction_hash or "",
        report_hash=report.report_hash(),
        verified=report.verified,
        worker_result_hash=_worker_result_hash(results),
    )


def _event(index: int) -> dict[str, object]:
    region = index % 17
    ride = index // 3
    return {
        "event_id": f"load.event.{index:06d}",
        "routing_key": f"ride.{ride:06d}.region.{region:02d}",
        "routing_scope": "rides",
        "payload": {
            "dropoff_cell": f"dropoff.{(index * 7) % 113:03d}",
            "pickup_cell": f"pickup.{(index * 5) % 97:03d}",
            "rider_id": f"rider.{index % 1009:04d}",
            "sequence_marker": index,
        },
    }


def _partition_order_hash(records: list[Any]) -> str:
    return _canonical_hash(
        [
            {
                "event_id": record.event_id,
                "partition_id": record.partition_id,
                "sequence": record.sequence,
            }
            for record in sorted(
                records,
                key=lambda item: (
                    item.partition_id,
                    item.sequence,
                    item.event_id,
                ),
            )
        ]
    )


def _worker_result_hash(results: list[Any]) -> str:
    return _canonical_hash(
        [
            result.canonical_dict()
            for result in sorted(
                results,
                key=lambda item: (
                    item.partition_id,
                    item.partition_sequence,
                    item.event_id,
                ),
            )
        ]
    )


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def _require_event_count(value: int) -> None:
    if not isinstance(value, int) or value <= 0:
        raise LoadProofError("event_count must be a positive int")


def _require_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise LoadProofError(f"{field} must be a non-empty string")
    return value
