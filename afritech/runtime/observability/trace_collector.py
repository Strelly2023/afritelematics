"""
AfriTech Trace Collector

PURPOSE:
--------
Collects and manages execution traces across the runtime.

Responsibilities:
- create and manage traces
- attach spans to traces
- track execution timing
- provide snapshot visibility

CRITICAL LAW:
-------------
Trace Collector MAY:
- record traces and spans
- track execution timing

Trace Collector may NOT:
- modify event data
- affect execution behavior
- introduce non-determinism
"""

import time
import uuid


# ============================================================
# ✅ TRACE COLLECTOR CLASS
# ============================================================

class TraceCollector:
    """
    Collects and manages traces.

    A trace represents:
    - one event lifecycle
    - composed of multiple spans (steps)
    """

    def __init__(self):
        # trace_id → trace data
        self.traces = {}

    # ========================================================
    # ✅ START TRACE
    # ========================================================

    def start_trace(self, event_id: str):
        """
        Initialize a new trace.

        Returns:
            trace_id
        """

        trace_id = str(uuid.uuid4())

        self.traces[trace_id] = {
            "trace_id": trace_id,
            "event_id": event_id,
            "start_time": time.time(),
            "end_time": None,
            "spans": [],
            "metadata": {},
        }

        return trace_id

    # ========================================================
    # ✅ END TRACE
    # ========================================================

    def end_trace(self, trace_id: str):
        """
        Mark trace as completed.
        """

        trace = self.traces.get(trace_id)

        if not trace:
            return

        trace["end_time"] = time.time()

    # ========================================================
    # ✅ ADD SPAN
    # ========================================================

    def add_span(self, trace_id: str, span: dict):
        """
        Attach a span to a trace.

        Span must already be finalized.
        """

        trace = self.traces.get(trace_id)

        if not trace:
            return

        if not isinstance(span, dict):
            raise TypeError("Span must be a dictionary")

        trace["spans"].append(span)

    # ========================================================
    # ✅ GET TRACE
    # ========================================================

    def get_trace(self, trace_id: str):
        """
        Retrieve a single trace.
        """

        return self.traces.get(trace_id)

    # ========================================================
    # ✅ LIST TRACES
    # ========================================================

    def list_traces(self):
        """
        Return all trace IDs.
        """

        return list(self.traces.keys())

    # ========================================================
    # ✅ ADD METADATA TO TRACE
    # ========================================================

    def add_metadata(self, trace_id: str, key: str, value):
        """
        Attach metadata to a trace (non-semantic).
        """

        if trace_id not in self.traces:
            return

        self.traces[trace_id]["metadata"][key] = value

    # ========================================================
    # ✅ TRACE DURATION
    # ========================================================

    def get_duration(self, trace_id: str):
        """
        Compute duration of trace.
        """

        trace = self.traces.get(trace_id)

        if not trace:
            return None

        start = trace.get("start_time")
        end = trace.get("end_time")

        if not end:
            return None

        return end - start

    # ========================================================
    # ✅ TRACE SUMMARY
    # ========================================================

    def summarize_trace(self, trace_id: str):
        """
        Provide lightweight trace summary.
        """

        trace = self.traces.get(trace_id)

        if not trace:
            return None

        return {
            "event_id": trace.get("event_id"),
            "duration": self.get_duration(trace_id),
            "span_count": len(trace.get("spans", [])),
        }

    # ========================================================
    # ✅ FULL SNAPSHOT
    # ========================================================

    def snapshot(self):
        """
        Full snapshot of all traces.

        Safe copy (read-only intent).
        """

        return {k: dict(v) for k, v in self.traces.items()}

    # ========================================================
    # ✅ CLEAR TRACES
    # ========================================================

    def clear(self):
        """
        Remove all traces (for testing/reset).
        """

        self.traces.clear()

    # ========================================================
    # ✅ VALIDATION
    # ============================================================

    def validate_trace(self, trace_id: str):
        """
        Validate structure of a trace.
        """

        trace = self.traces.get(trace_id)

        if not trace:
            raise Exception(f"[TRACE ERROR] Trace not found: {trace_id}")

        required = ["event_id", "start_time", "spans"]

        for field in required:
            if field not in trace:
                raise Exception(
                    f"[TRACE ERROR] Missing field: {field}"
                )

        if not isinstance(trace["spans"], list):
            raise Exception("[TRACE ERROR] Invalid spans structure")

        return True

    # ========================================================
    # ✅ DETERMINISM CHECK
    # ============================================================

    def validate_trace_integrity(self, trace_id: str):
        """
        Ensure trace integrity (no corruption).
        """

        trace = self.get_trace(trace_id)

        if not trace:
            raise Exception("[TRACE ERROR] Trace missing")

        # Ensure spans are ordered
        previous_time = 0

        for span in trace["spans"]:
            start = span.get("start")

            if start and start < previous_time:
                raise Exception(
                    "[TRACE ERROR] Non-deterministic span ordering"
                )

            previous_time = start if start else previous_time

        return True

    # ========================================================
    # ✅ TRACE FILTER
    # ============================================================

    def filter_traces(self, predicate):
        """
        Filter traces based on a predicate.

        predicate(trace) -> bool
        """

        return {
            tid: trace
            for tid, trace in self.traces.items()
            if predicate(trace)
        }

    # ========================================================
    # ✅ TRACE DEBUG VIEW
    # ============================================================

    def trace_debug(self, trace_id: str):
        """
        Human-readable simplified trace view.
        """

        trace = self.get_trace(trace_id)

        if not trace:
            return None

        spans = [
            {
                "name": s.get("name"),
                "duration": s.get("duration"),
            }
            for s in trace.get("spans", [])
        ]

        return {
            "event_id": trace.get("event_id"),
            "duration": self.get_duration(trace_id),
            "spans": spans,
        }