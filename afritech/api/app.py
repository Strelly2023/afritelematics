"""FastAPI entrypoint for the deterministic MVP production pipeline."""

from __future__ import annotations
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ============================================================
# API LAYERS
# ============================================================

from afritech.api.auth.jwt_device_auth import build_auth_router
from afritech.api.ingestion.event_ingestion import (
    EventIngestionAPI,
    build_router,
)
from afritech.api.realtime.ws_server import WebSocketHub
from afritech.api.trace_api import build_trace_router
from afritech.api.system_status import build_system_status_router

# ============================================================
# EDGE PIPELINE
# ============================================================

from afritech.edge.adapter.runtime_adapter import adapt_request
from afritech.edge.adapter.validation import validate_adapted_request
from afritech.edge.ingestion.queue_ingestor import ingest_event
from afritech.edge.normalization.normalizer import normalize_input
from afritech.edge.normalization.validation import validate_normalized_input

# ============================================================
# EXECUTION LAYER
# ============================================================

from afritech.execution.partition.router import get_partition
from afritech.execution.queue.partitioned_queue import PartitionedQueue
from afritech.execution.worker.worker_pool import WorkerPool


# ============================================================
# APPLICATION INIT
# ============================================================

app = FastAPI(title="AfriTech Deterministic MVP Pipeline")

# ✅ CORS (IMPORTANT for React dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CORE SYSTEM
# ============================================================

queue = PartitionedQueue(num_partitions=8)
worker_pool = WorkerPool(queue)

mobile_event_ingestion = EventIngestionAPI(secret="pilot-secret")
realtime_hub = WebSocketHub()


# ============================================================
# ROUTERS
# ============================================================

# ✅ Core ingestion API
app.include_router(build_router(mobile_event_ingestion))

# ✅ Auth API
app.include_router(build_auth_router())

# ✅ Trace API (dashboard critical)
trace_router = build_trace_router()
app.include_router(trace_router)

# ✅ System status API
app.include_router(build_system_status_router())


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root() -> dict[str, Any]:
    """Report bounded pilot API status without claiming product readiness."""
    return {
        "status": "active",
        "service": "AfriTech Deterministic MVP Pipeline",
        "classification": "controlled_pilot_api",
        "product_ready": False,
        "docs": "/docs",
        "event_ingestion": "/v1/events",
        "trace_api": "/v1/traces",
    }


# ============================================================
# WEBSOCKET ADAPTER
# ============================================================

class FastAPIWebSocketClient:
    """Adapter so the observation-only hub can publish to FastAPI sockets."""

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    async def send_json(self, message: dict[str, Any]) -> None:
        await self.websocket.send_json(message)


# ============================================================
# REALTIME WEBSOCKET
# ============================================================

@app.websocket("/ws/{ride_id}")
async def ride_projection_socket(websocket: WebSocket, ride_id: str) -> None:
    """Subscribe a client to observation-only projected ride state."""

    await websocket.accept()
    client = FastAPIWebSocketClient(websocket)
    realtime_hub.subscribe(ride_id, client)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        realtime_hub.unsubscribe(ride_id, client)


# ============================================================
# REALTIME PUBLISH (PILOT)
# ============================================================

@app.post("/v1/realtime/ride/{ride_id}/projection")
async def publish_ride_projection(
    ride_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Pilot-only projection publisher; does not mutate source-of-truth."""

    data = dict(payload.get("data", payload))
    message = await realtime_hub.publish_state_update(ride_id, data)

    return {
        "status": "published",
        "message": message,
    }


# ============================================================
# EDGE PROCESSING PIPELINE
# ============================================================

@app.post("/process")
def process(payload: dict[str, Any]) -> dict[str, Any]:
    """Process one external request through the deterministic edge pipeline."""

    raw_input = {
        "request_id": str(payload.get("request_id")),
        "user_id": str(payload.get("user_id")),
        "timestamp": int(payload.get("timestamp", 0)),
        "payload": dict(payload),
    }

    # Edge → Adapter
    adapted = adapt_request(raw_input)
    validate_adapted_request(adapted)

    # Edge → Normalization
    normalized = normalize_input(adapted)
    validate_normalized_input(normalized)

    # Execution routing
    partition_id = get_partition(normalized, queue.num_partitions)

    # Ingestion
    ingest_event(normalized, queue, partition_id=partition_id)

    return {
        "status": "accepted",
        "request_id": normalized["request_id"],
        "partition_id": partition_id,
    }


# ============================================================
# WORKER CONTROL
# ============================================================

@app.post("/workers/drain")
def drain_workers(partition_id: int | None = None) -> dict[str, Any]:
    """Run deterministic worker cycles for queued events."""

    outputs = worker_pool.drain(partition_id=partition_id)

    return {
        "status": "drained",
        "processed": len(outputs),
        "outputs": [result.outputs for result in outputs],
    }
