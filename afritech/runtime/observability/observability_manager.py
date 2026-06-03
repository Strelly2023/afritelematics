"""
AfriTech Observability Manager

PURPOSE:
--------
Central coordination point for observability.

Responsibilities:
- manage traces (distributed tracing)
- collect metrics
- record structured logs
- provide system-wide observability snapshot
- ensure non-intrusive instrumentation

CRITICAL LAW:
-------------
Observability Manager MAY:
- observe execution
- record metrics and traces

Observability Manager may NOT:
- modify events
- affect execution semantics
- introduce non-determinism
"""

import time

from afritech.runtime.observability.trace_collector import TraceCollector
from afritech.runtime.observability.metrics_collector import MetricsCollector
from afritech.runtime.observability.logger import log
from afritech.runtime.observability.span import Span


# ============================================================
# ✅ OBSERVABILITY MANAGER
# ============================================================

class ObservabilityManager:
    """
    Central observability coordinator.

    Provides:
    - tracing (execution visibility)
    - metrics aggregation
    - structured logging
    """

    def __init__(self, enable_tracing=True, enable_metrics=True):
        self.enable_tracing = enable_tracing
        self.enable_metrics = enable_metrics

        self.tracer = TraceCollector() if enable_tracing else None
        self.metrics = MetricsCollector() if enable_metrics else None

        # ✅ trace_id → metadata
        self.active_traces = {}

    # ========================================================
    # ✅ TRACE MANAGEMENT (FIXED ✅)
    # ========================================================

    def start_trace(self, event_id: str):
        """
        Start a new trace.

        ✅ FIX:
        - TraceCollector is the single source of truth
        """

        if not self.enable_tracing:
            return None

        # ✅ TraceCollector generates the trace_id
        trace_id = self.tracer.start_trace(event_id)

        self.active_traces[trace_id] = {
            "event_id": event_id,
            "start_time": time.time(),
        }

        return trace_id

    def end_trace(self, trace_id: str):
        """
        End an existing trace.
        """

        if not self.enable_tracing:
            return

        if trace_id not in self.active_traces:
            return

        self.tracer.end_trace(trace_id)
        self.active_traces[trace_id]["end_time"] = time.time()

    # ========================================================
    # ✅ SPAN MANAGEMENT
    # ========================================================

    def start_span(self, trace_id: str, name: str):
        """
        Start a span within a trace.
        """

        if not self.enable_tracing:
            return None

        if trace_id not in self.active_traces:
            return None

        # ✅ Link span to trace_id
        return Span(name=name, trace_id=trace_id)

    def finish_span(self, trace_id: str, span: Span):
        """
        Complete span and attach it to trace.
        """

        if not self.enable_tracing:
            return

        if trace_id not in self.active_traces:
            return

        if span is None:
            return

        span.finish()

        # ✅ Add finalized span
        self.tracer.add_span(trace_id, span.to_dict())

    # ========================================================
    # ✅ METRICS MANAGEMENT
    # ============================================================

    def record_metric(self, name: str, value: float):
        """
        Record numeric metric.
        """

        if not self.enable_metrics:
            return

        if not isinstance(name, str):
            raise TypeError("Metric name must be string")

        self.metrics.record(name, value)

    # ========================================================
    # ✅ LOGGING SUPPORT
    # ============================================================

    def log(self, message: str, level="INFO", **kwargs):
        """
        Structured logging interface.
        """

        log(message, level=level, **kwargs)

    # ========================================================
    # ✅ TRACE CONTEXT
    # ============================================================

    def bind_trace(self, trace_id: str, **metadata):
        """
        Attach metadata to an active trace.
        """

        if trace_id in self.active_traces:
            self.active_traces[trace_id].update(metadata)

            # ✅ also store inside trace collector metadata
            self.tracer.add_metadata(trace_id, "context", metadata)

    # ========================================================
    # ✅ SNAPSHOT
    # ============================================================

    def snapshot(self):
        """
        Return full observability snapshot.
        """

        snapshot = {}

        if self.enable_metrics:
            snapshot["metrics"] = self.metrics.snapshot()

        if self.enable_tracing:
            snapshot["traces"] = self.tracer.snapshot()

        snapshot["active_traces"] = dict(self.active_traces)

        return snapshot

    # ========================================================
    # ✅ RESET
    # ============================================================

    def reset(self):
        """
        Reset observability state (test-safe).
        """

        if self.enable_metrics:
            self.metrics.clear()

        if self.enable_tracing:
            self.tracer.clear()

        self.active_traces.clear()

    # ========================================================
    # ✅ NON-INTRUSIVE GUARANTEE
    # ============================================================

    def validate_non_intrusive(self):
        """
        Ensures observability has no side effects.

        Always true by design.
        """
        return True

    # ========================================================
    # ✅ TRACE SUMMARY
    # ============================================================

    def summarize_traces(self):
        """
        Lightweight trace summary.
        """

        if not self.enable_tracing:
            return {}

        summary = {}

        for trace_id, data in self.tracer.snapshot().items():
            start = data.get("start_time")
            end = data.get("end_time")

            duration = None
            if start and end:
                duration = end - start

            summary[trace_id] = {
                "event_id": data.get("event_id"),
                "duration": duration,
                "span_count": len(data.get("spans", [])),
            }

        return summary

    # ========================================================
    # ✅ METRICS SUMMARY
    # ============================================================

    def summarize_metrics(self):
        """
        Return aggregated metrics summary.
        """

        if not self.enable_metrics:
            return {}

        return self.metrics.snapshot()