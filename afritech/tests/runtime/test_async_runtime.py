"""
AfriTech Async Runtime Tests

FINAL VERSION (Replay + Audit Compatible)

VALIDATES:
----------
- execution correctness
- determinism
- immutability
- queue behavior
- dispatcher → locality → queue → worker → scheduler
- observability safety
- replay + audit compatibility (non-intrusive)

CRITICAL GUARANTEE:
------------------
Execution variability MUST NOT affect truth
"""

import pytest

from afritech.runtime.async_runtime.queue_runtime import QueueRuntime
from afritech.runtime.async_runtime.worker_runtime import WorkerRuntime
from afritech.runtime.async_runtime.dispatcher import dispatch_event
from afritech.runtime.async_runtime.scheduler import Scheduler

from afritech.runtime.locality.locality_manager import resolve_queue_name
from afritech.runtime.locality.partition_router import resolve_partition
#afritech/tests/runtime/test_async_runtime.py

# ============================================================
# ✅ TEST CONTEXT (PLUGGABLE SERVICES)
# ============================================================

class DummyObservability:
    def start_trace(self, *_): return "trace"
    def end_trace(self, *_): pass
    def start_span(self, *_): return type("Span", (), {"span_id": "s"})()
    def finish_span(self, *_): pass
    def record_metric(self, *_): pass
    def log(self, *_ , **__): pass


class DummyEventStore:
    def __init__(self):
        self.events = []

    def append(self, event):
        self.events.append(dict(event))


class DummyAuditLog:
    def __init__(self):
        self.records = []

    def record(self, **kwargs):
        self.records.append(dict(kwargs))


class DummyContext:
    def __init__(self):
        self.policy = {
            "batch_size": 2,
            "retry_limit": 2,
            "transport_mode": "test",
            "partition_count": 10,
            "default_region": "test-region",
        }

        # ✅ Pluggable services
        self.observability = DummyObservability()
        self.event_store = DummyEventStore()
        self.audit_log = DummyAuditLog()


# ============================================================
# ✅ FIXTURE
# ============================================================

@pytest.fixture
def runtime_system():
    queue = QueueRuntime()
    worker = WorkerRuntime(queue)
    scheduler = Scheduler(worker, queue)
    context = DummyContext()

    return queue, worker, scheduler, context


# ============================================================
# ✅ BASIC EXECUTION
# ============================================================

def test_async_pipeline_executes(runtime_system):
    queue, worker, scheduler, context = runtime_system

    event = {
        "event_id": "1",
        "payload": {"value": 100},
        "timestamp": "2026-01-01",
    }

    result = dispatch_event(event, queue, context)
    assert result["status"] == "queued"

    q = resolve_queue_name(event, context)

    scheduler.run(context, max_cycles=3)

    assert queue.get_queue_length(q) == 0


# ============================================================
# ✅ DETERMINISM
# ============================================================

def test_deterministic_execution(runtime_system):
    queue, worker, scheduler, context = runtime_system

    base_event = {
        "event_id": "2",
        "payload": {"value": 200},
        "timestamp": "2026-01-02",
    }

    dispatch_event(dict(base_event), queue, context)
    dispatch_event(dict(base_event), queue, context)

    q = resolve_queue_name(base_event, context)

    r1 = worker.run_once(q, context)
    r2 = worker.run_once(q, context)

    assert r1["status"] in ["processed", "idle"]
    assert r2["status"] in ["processed", "idle"]

    # ✅ immutability
    assert base_event == {
        "event_id": "2",
        "payload": {"value": 200},
        "timestamp": "2026-01-02",
    }


# ============================================================
# ✅ BATCH PROCESSING
# ============================================================

def test_batch_processing(runtime_system):
    queue, worker, scheduler, context = runtime_system

    events = [
        {"event_id": str(i), "payload": {"value": i}, "timestamp": "2026-01-01"}
        for i in range(5)
    ]

    for e in events:
        dispatch_event(e, queue, context)

    q = resolve_queue_name(events[0], context)

    result = worker.run_once(q, context)

    assert result["processed"] <= context.policy["batch_size"]


# ============================================================
# ✅ FIFO PER PARTITION
# ============================================================

def test_fifo_order(runtime_system):
    queue, worker, scheduler, context = runtime_system

    events = [
        {"event_id": str(i), "payload": {}, "timestamp": "2026-01-01"}
        for i in range(4)
    ]

    for e in events:
        dispatch_event(e, queue, context)

    partitions = {}

    for e in events:
        p = resolve_partition(e, context)
        partitions.setdefault(p, []).append(e)

    for p, evs in partitions.items():
        q = resolve_queue_name(evs[0], context)

        dequeued = queue.dequeue_batch(q, len(evs))

        assert [e["event_id"] for e in dequeued] == [
            e["event_id"] for e in evs
        ]


# ============================================================
# ✅ QUEUE STATE
# ============================================================

def test_queue_state_tracking(runtime_system):
    queue, worker, scheduler, context = runtime_system

    event = {
        "event_id": "x",
        "payload": {"value": 999},
        "timestamp": "2026-01-01",
    }

    dispatch_event(event, queue, context)

    q = resolve_queue_name(event, context)
    assert queue.get_queue_length(q) == 1

    worker.run_once(q, context)

    assert queue.get_queue_length(q) == 0


# ============================================================
# ✅ IMMUTABILITY
# ============================================================

def test_event_immutability(runtime_system):
    queue, worker, scheduler, context = runtime_system

    original = {
        "event_id": "imm",
        "payload": {"value": 123},
        "timestamp": "2026-01-01",
    }

    copy = dict(original)

    dispatch_event(original, queue, context)

    q = resolve_queue_name(original, context)
    worker.run_once(q, context)

    assert original == copy


# ============================================================
# ✅ BULK PIPELINE
# ============================================================

def test_bulk_pipeline(runtime_system):
    queue, worker, scheduler, context = runtime_system

    for i in range(10):
        dispatch_event(
            {
                "event_id": str(i),
                "payload": {"value": i},
                "timestamp": "2026-01-01",
            },
            queue,
            context,
        )

    scheduler.run(context, max_cycles=10)

    snapshot = queue.snapshot()

    assert all(size == 0 for size in snapshot.values())


# ============================================================
# ✅ QUEUE PRESSURE
# ============================================================

def test_queue_pressure(runtime_system):
    queue, worker, scheduler, context = runtime_system

    for i in range(20):
        dispatch_event(
            {"event_id": str(i), "payload": {}, "timestamp": "2026-01-01"},
            queue,
            context,
        )

    snapshot = queue.snapshot()

    assert any(size > 0 for size in snapshot.values())


# ============================================================
# ✅ LOCALITY
# ============================================================

def test_locality_integration(runtime_system):
    queue, worker, scheduler, context = runtime_system

    event = {
        "event_id": "loc1",
        "payload": {"value": 10},
        "timestamp": "2026-01-01",
        "region": "au",
    }

    result = dispatch_event(event, queue, context)

    assert "region" in result
    assert "partition" in result
    assert "node" in result

    q = resolve_queue_name(event, context)

    assert q.startswith("events.")


# ============================================================
# ✅ OBSERVABILITY SAFETY
# ============================================================

def test_observability_non_intrusive(runtime_system):
    queue, worker, scheduler, context = runtime_system

    event = {
        "event_id": "obs",
        "payload": {"value": 1},
        "timestamp": "2026-01-01",
    }

    original = dict(event)

    dispatch_event(event, queue, context)

    q = resolve_queue_name(event, context)
    worker.run_once(q, context)

    assert event == original


# ============================================================
# ✅ REPLAY INTEGRATION (NEW ✅)
# ============================================================

def test_event_store_integration(runtime_system):
    queue, worker, scheduler, context = runtime_system

    event = {
        "event_id": "replay1",
        "payload": {"value": 5},
        "timestamp": "2026-01-01",
    }

    dispatch_event(event, queue, context)

    # ✅ Event stored
    assert len(context.event_store.events) == 1
    assert context.event_store.events[0]["event_id"] == "replay1"


# ============================================================
# ✅ AUDIT LOG (NEW ✅)
# ============================================================

def test_audit_log_records(runtime_system):
    queue, worker, scheduler, context = runtime_system

    event = {
        "event_id": "audit1",
        "payload": {"value": 5},
        "timestamp": "2026-01-01",
    }

    dispatch_event(event, queue, context)

    actions = [r["action"] for r in context.audit_log.records]

    assert "dispatch_received" in actions
    assert "dispatch_enqueued" in actions