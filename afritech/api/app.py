"""FastAPI entrypoint for the deterministic MVP production pipeline."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from afritech.edge.adapter.runtime_adapter import adapt_request
from afritech.edge.adapter.validation import validate_adapted_request
from afritech.edge.ingestion.queue_ingestor import ingest_event
from afritech.edge.normalization.normalizer import normalize_input
from afritech.edge.normalization.validation import validate_normalized_input
from afritech.execution.partition.router import get_partition
from afritech.execution.queue.partitioned_queue import PartitionedQueue
from afritech.execution.worker.worker_pool import WorkerPool


app = FastAPI(title="AfriTech Deterministic MVP Pipeline")
queue = PartitionedQueue(num_partitions=8)
worker_pool = WorkerPool(queue)


@app.post("/process")
def process(payload: dict[str, Any]) -> dict[str, Any]:
    """Process one external request through the declared edge pipeline."""

    raw_input = {
        "request_id": str(payload.get("request_id")),
        "user_id": str(payload.get("user_id")),
        "timestamp": int(payload.get("timestamp", 0)),
        "payload": dict(payload),
    }

    adapted = adapt_request(raw_input)
    validate_adapted_request(adapted)

    normalized = normalize_input(adapted)
    validate_normalized_input(normalized)

    partition_id = get_partition(normalized, queue.num_partitions)
    ingest_event(normalized, queue, partition_id=partition_id)

    return {
        "status": "accepted",
        "request_id": normalized["request_id"],
        "partition_id": partition_id,
    }


@app.post("/workers/drain")
def drain_workers(partition_id: int | None = None) -> dict[str, Any]:
    """Run deterministic worker cycles for admitted queue events."""

    outputs = worker_pool.drain(partition_id=partition_id)
    return {
        "status": "drained",
        "processed": len(outputs),
        "outputs": outputs,
    }
