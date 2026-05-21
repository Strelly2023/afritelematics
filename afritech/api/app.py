"""FastAPI entrypoint for the deterministic MVP production pipeline."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from afritech.core.runtime.worker.worker import process_event
from afritech.edge.adapter.runtime_adapter import adapt_request
from afritech.edge.adapter.validation import validate_adapted_request
from afritech.edge.ingestion.queue_ingestor import ingest_event
from afritech.edge.normalization.normalizer import normalize_input
from afritech.edge.normalization.validation import validate_normalized_input
from afritech.execution.queue.simple_queue import SimpleQueue


app = FastAPI(title="AfriTech Deterministic MVP Pipeline")
queue = SimpleQueue()


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

    ingest_event(normalized, queue)

    event = queue.consume()
    return process_event(
        event,
        flow_trace={"stages": ["adapter", "normalization", "ingestion"]},
    )

