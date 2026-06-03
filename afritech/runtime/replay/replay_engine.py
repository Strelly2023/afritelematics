"""
AfriTech Replay Engine (GA Elite - Production Grade)

Deterministic + Pure Replay Implementation
"""

from typing import List, Dict, Optional
import copy
import hashlib
import json

from afritech.runtime.async_runtime.dispatcher import dispatch_event


# ============================================================
# ✅ REPLAY ENGINE
# ============================================================

class ReplayEngine:

    def __init__(self, event_store):
        self.event_store = event_store

    # ========================================================
    # ✅ INTERNAL UTILITIES
    # ========================================================

    def _deep_copy(self, event: Dict) -> Dict:
        return copy.deepcopy(event)

    def _ordered(self, events: List[Dict]) -> List[Dict]:
        return sorted(events, key=lambda e: (e.get("timestamp", 0), e.get("event_id")))

    def _hash(self, data) -> str:
        return hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()

    def _validate_event_store(self):
        required_methods = [
            "get_all", "get_by_id", "get_after", "get_range", "count"
        ]
        for m in required_methods:
            if not hasattr(self.event_store, m):
                raise Exception(f"[REPLAY ERROR] Missing method: {m}")

    # ========================================================
    # ✅ ISOLATION (CRITICAL ✅)
    # ========================================================

    def _isolate_context(self, context):
        """
        Remove side-effect components during replay.
        """
        original_store = getattr(context, "event_store", None)
        original_audit = getattr(context, "audit_log", None)

        context.event_store = None
        context.audit_log = None

        return original_store, original_audit

    def _restore_context(self, context, store, audit):
        context.event_store = store
        context.audit_log = audit

    def _snapshot_queue(self, queue_runtime):
        """
        Snapshot queue sizes only.
        """
        snapshot = queue_runtime.snapshot()

        # drain queues
        for q in snapshot:
            while queue_runtime.get_queue_length(q) > 0:
                queue_runtime.dequeue_batch(q, 1000)

        return snapshot

    def _restore_queue(self, queue_runtime, snapshot):
        """
        Restore only structure (not exact events).
        """
        for q, count in snapshot.items():
            for _ in range(count):
                queue_runtime.enqueue(q, {"__replay_placeholder__": True})

    # ========================================================
    # ✅ CORE REPLAY WRAPPER
    # ========================================================

    def _execute(self, events, queue_runtime, context):
        results = []

        original_store, original_audit = self._isolate_context(context)
        queue_snapshot = self._snapshot_queue(queue_runtime)

        try:
            for event in events:
                result = dispatch_event(
                    self._deep_copy(event),
                    queue_runtime,
                    context,
                )
                results.append(result)

        finally:
            self._restore_context(context, original_store, original_audit)
            self._restore_queue(queue_runtime, queue_snapshot)

        return results

    # ========================================================
    # ✅ REPLAY OPERATIONS
    # ========================================================

    def replay_all(self, queue_runtime, context) -> List:
        events = self._ordered(self.event_store.get_all())
        return self._execute(events, queue_runtime, context)

    def replay_event(self, event_id: str, queue_runtime, context) -> Optional:
        events = self.event_store.get_by_id(event_id)
        if not events:
            return None
        return self._execute([events[0]], queue_runtime, context)[0]

    def replay_last(self, queue_runtime, context) -> Optional:
        events = self._ordered(self.event_store.get_all())
        if not events:
            return None
        return self._execute([events[-1]], queue_runtime, context)[0]

    def replay_after(self, timestamp, queue_runtime, context) -> List:
        events = self._ordered(self.event_store.get_after(timestamp))
        return self._execute(events, queue_runtime, context)

    def replay_range(self, start_ts, end_ts, queue_runtime, context) -> List:
        if start_ts > end_ts:
            raise ValueError("start_ts must be <= end_ts")

        events = self._ordered(
            self.event_store.get_range(start_ts, end_ts)
        )
        return self._execute(events, queue_runtime, context)

    # ========================================================
    # ✅ PREVIEW
    # ========================================================

    def preview(self) -> List:
        return self._ordered(self.event_store.get_all())

    def count(self) -> int:
        return self.event_store.count()

    # ========================================================
    # ✅ VALIDATION
    # ========================================================

    def validate(self) -> bool:
        self._validate_event_store()
        return True

    # ========================================================
    # ✅ DETERMINISM VALIDATION (FIXED ✅)
    # ========================================================

    def validate_determinism(self, queue_runtime, context) -> bool:
        events = self._ordered(self.event_store.get_all())

        run1 = self._execute(events, queue_runtime, context)
        run2 = self._execute(events, queue_runtime, context)

        if self._hash(run1) != self._hash(run2):
            raise Exception("[REPLAY ERROR] Non-deterministic replay")

        return True

    # ========================================================
    # ✅ TRACE REPLAY
    # ========================================================

    def trace_replay(self, queue_runtime, context) -> Dict:
        results = self.replay_all(queue_runtime, context)

        obs = getattr(context, "observability", None)

        return {
            "replayed_events": len(results),
            "metrics": obs.snapshot() if obs else None,
        }
    # ============================================================
# ✅ PHASE 0 COMPATIBILITY REPLAY
# ============================================================

def replay(fn, trace):
    """
    Minimal deterministic replay surface for Phase 0.

    Constitutional law:
        no replay -> no legitimacy
    """

    required = {
        "input",
        "output",
    }

    missing = required.difference(trace)

    if missing:
        raise Exception(
            "No trace -> no replay"
        )

    replay_output = fn(trace["input"])

    if replay_output != trace["output"]:
        raise Exception(
            "No replay -> no legitimacy"
        )

    return True