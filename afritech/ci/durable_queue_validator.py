"""Validate durable queue proof for production readiness."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Any

from afritech.distributed.partition.partition_assignment import assign_partition
from afritech.distributed.partition.partition_registry import default_partition_registry
from afritech.distributed.queue.distributed_queue_adapter import build_queue_record
from afritech.execution.queue.durable_queue import (
    AUTHORITY_DISCLAIMER,
    DurableQueueAdapter,
    DurableQueueError,
    restore_durable_queue,
)


class DurableQueueValidationError(RuntimeError):
    """Raised when durable queue proof fails."""


@dataclass(frozen=True)
class DurableQueueProofReport:
    delivery_hash: str
    restored_delivery_hash: str
    mutation_rejected: bool
    duplicate_rejected: bool
    authority_disclaimer: str
    record_count: int

    @property
    def verified(self) -> bool:
        return (
            self.delivery_hash == self.restored_delivery_hash
            and self.mutation_rejected
            and self.duplicate_rejected
            and self.authority_disclaimer == AUTHORITY_DISCLAIMER
            and self.record_count > 0
        )

    def canonical_dict(self) -> dict[str, object]:
        return {
            "authority_disclaimer": self.authority_disclaimer,
            "delivery_hash": self.delivery_hash,
            "duplicate_rejected": self.duplicate_rejected,
            "mutation_rejected": self.mutation_rejected,
            "record_count": self.record_count,
            "restored_delivery_hash": self.restored_delivery_hash,
            "schema": "afritech.durable_queue_proof_report.v1",
            "verified": self.verified,
        }

    def report_hash(self) -> str:
        return _canonical_hash(self.canonical_dict())


def validate() -> DurableQueueProofReport:
    report = run_durable_queue_proof()
    if not report.verified:
        raise DurableQueueValidationError("durable queue proof failed")
    return report


def run_durable_queue_proof() -> DurableQueueProofReport:
    registry = default_partition_registry()
    queue = DurableQueueAdapter(registry=registry)
    records = _records(registry)
    queue.publish_many(records)
    rows = queue.backend.rows()
    restored = restore_durable_queue(registry=registry, rows=rows)

    mutation_rejected = _mutation_rejected(registry, rows)
    duplicate_rejected = _duplicate_rejected(queue, records[0])

    return DurableQueueProofReport(
        authority_disclaimer=AUTHORITY_DISCLAIMER,
        delivery_hash=queue.delivery_hash(),
        duplicate_rejected=duplicate_rejected,
        mutation_rejected=mutation_rejected,
        record_count=len(records),
        restored_delivery_hash=restored.delivery_hash(),
    )


def _records(registry):
    partition_sequences: dict[str, int] = {}
    built = []
    for index in range(9):
        routing_key = f"ride.durable.{index % 4:02d}"
        event = {
            "event_id": f"durable.event.{index:03d}",
            "payload": {
                "rider_id": f"rider.{index:03d}",
                "sequence_marker": index,
            },
            "routing_key": routing_key,
            "routing_scope": "rides",
        }
        assignment = assign_partition(
            routing_key=routing_key,
            routing_scope="rides",
            registry=registry,
        )
        sequence = partition_sequences.get(assignment.partition_id, 0)
        partition_sequences[assignment.partition_id] = sequence + 1
        built.append(
            build_queue_record(
                event_id=event["event_id"],
                sequence=sequence,
                normalized_payload_hash=_canonical_hash(event["payload"]),
                event=event,
                assignment=assignment,
                registry=registry,
            )
        )
    return tuple(built)


def _mutation_rejected(registry, rows) -> bool:
    mutated = [dict(row) for row in rows]
    mutated[0] = dict(mutated[0])
    mutated[0]["record"] = dict(mutated[0]["record"])
    mutated[0]["record"]["event_id"] = "durable.event.tampered"
    try:
        restore_durable_queue(registry=registry, rows=mutated)
    except DurableQueueError:
        return True
    return False


def _duplicate_rejected(queue: DurableQueueAdapter, record) -> bool:
    try:
        queue.publish(record)
    except DurableQueueError:
        return True
    return False


def _canonical_hash(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def main() -> int:
    try:
        report = validate()
    except DurableQueueValidationError as exc:
        print(f"Durable queue validation FAILED: {exc}")
        return 1
    print(
        "Durable queue validation PASSED: "
        f"delivery_hash={report.delivery_hash} "
        f"report_hash={report.report_hash()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
