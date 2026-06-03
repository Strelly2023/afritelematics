"""
AfriTech Replay Engine Tests

PURPOSE:
--------
Validate replay system:

- event storage correctness
- deterministic replay
- time-based replay
- audit consistency
- non-intrusive guarantees

CRITICAL GUARANTEE:
------------------
Replay MUST produce identical behavior without mutating original events
"""

import pytest

from afritech.runtime.async_runtime.queue_runtime import QueueRuntime
from afritech.runtime.async_runtime.worker_runtime import WorkerRuntime
from afritech.runtime.async_runtime.scheduler import Scheduler
from afritech.runtime.async_runtime.dispatcher import dispatch_event

from afritech.runtime.replay.event_store import EventStore
from afritech.runtime.replay.replay_engine import ReplayEngine
from afritech.runtime.replay.audit_log import AuditLog

#afritech/tests/runtime/test_replay.py
# ============================================================
# ✅ TEST CONTEXT
# ============================================================

class ReplayContext:
    def __init__(self):
        self.policy = {
            "batch_size": 2,
            "retry_limit": 2,
            "transport_mode": "test",
            "partition_count": 10,
            "default_region": "test-region",
        }

        self.event_store = EventStore()
        self.audit_log = AuditLog()


# ============================================================
# ✅ FIXTURE
# ============================================================

@pytest.fixture
def replay_system():
    queue = QueueRuntime()
    worker = WorkerRuntime(queue)
    scheduler = Scheduler(worker, queue)

    context = ReplayContext()

    replay_engine = ReplayEngine(context.event_store)

    return queue, worker, scheduler, context, replay_engine


# ============================================================
# ✅ EVENT STORAGE TEST
# ============================================================

def test_event_store_records_events(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    event = {
        "event_id": "1",
        "payload": {"value": 10},
        "timestamp": 1,
    }

    dispatch_event(event, queue, context)

    assert context.event_store.count() == 1


# ============================================================
# ✅ REPLAY ALL EVENTS
# ============================================================

def test_replay_all(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    for i in range(3):
        dispatch_event(
            {
                "event_id": str(i),
                "payload": {},
                "timestamp": i,
            },
            queue,
            context,
        )

    results = replay.replay_all(queue, context)

    assert len(results) == 3
    assert all(r["status"] == "queued" for r in results)


# ============================================================
# ✅ REPLAY SINGLE EVENT
# ============================================================

def test_replay_single_event(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    dispatch_event(
        {"event_id": "x", "payload": {}, "timestamp": 1},
        queue,
        context,
    )

    result = replay.replay_event("x", queue, context)

    assert result["event_id"] == "x"


# ============================================================
# ✅ REPLAY AFTER TIMESTAMP
# ============================================================

def test_replay_after(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    dispatch_event({"event_id": "a", "payload": {}, "timestamp": 1}, queue, context)
    dispatch_event({"event_id": "b", "payload": {}, "timestamp": 2}, queue, context)
    dispatch_event({"event_id": "c", "payload": {}, "timestamp": 3}, queue, context)

    results = replay.replay_after(1, queue, context)

    ids = [r["event_id"] for r in results]

    assert "b" in ids
    assert "c" in ids
    assert "a" not in ids


# ============================================================
# ✅ REPLAY RANGE
# ============================================================

def test_replay_range(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    for i in range(5):
        dispatch_event(
            {"event_id": str(i), "payload": {}, "timestamp": i},
            queue,
            context,
        )

    results = replay.replay_range(1, 3, queue, context)

    ids = [r["event_id"] for r in results]

    assert ids == ["1", "2", "3"]


# ============================================================
# ✅ REPLAY DOES NOT MUTATE ORIGINAL EVENTS
# ============================================================

def test_replay_immutability(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    event = {
        "event_id": "immut",
        "payload": {"value": 999},
        "timestamp": 1,
    }

    original = dict(event)

    dispatch_event(event, queue, context)

    replay.replay_all(queue, context)

    assert event == original


# ============================================================
# ✅ REPLAY DETERMINISM
# ============================================================

def test_replay_determinism(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    for i in range(3):
        dispatch_event(
            {"event_id": str(i), "payload": {}, "timestamp": i},
            queue,
            context,
        )

    run1 = replay.replay_all(queue, context)
    run2 = replay.replay_all(queue, context)

    assert run1 == run2


# ============================================================
# ✅ AUDIT LOG INTEGRATION
# ============================================================

def test_audit_log_integration(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    dispatch_event(
        {"event_id": "audit1", "payload": {}, "timestamp": 1},
        queue,
        context,
    )

    records = context.audit_log.get_all()

    actions = [r["action"] for r in records]

    assert "dispatch_received" in actions
    assert "dispatch_enqueued" in actions


# ============================================================
# ✅ PREVIEW (DRY RUN)
# ============================================================

def test_replay_preview(replay_system):
    queue, worker, scheduler, context, replay = replay_system

    dispatch_event(
        {"event_id": "p1", "payload": {}, "timestamp": 1},
        queue,
        context,
    )

    preview = replay.preview()

    assert len(preview) == 1
    assert preview[0]["event_id"] == "p1"